import csv
import io
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv

from .sheets_loader import get_sheets_service


load_dotenv()

PUBLIC_SITE_BASE_URL = os.environ.get("PUBLIC_SITE_BASE_URL", "https://sorravitsis.github.io/Frieght").rstrip("/")

TRACKING_KEYWORDS = (
    "ติดตาม",
    "สถานะ",
    "เลขพัสดุ",
    "เลขงาน",
    "เลขที่เอกสาร",
    "track",
    "tracking",
    "delivery",
    "job status",
    "job no",
)
TRACKING_PROMPT = "ส่งเลข DO มาให้ น้องโกดัง ได้เลยงับ"

TRACKING_HEADER_KEYWORDS = ("delivery", "jobno", "track", "เลขที่เอกสาร", "หมายเลขใบงาน")
AGENT_HEADER_KEYWORDS = ("agent", "carrier", "ขนส่ง")
STATUS_HEADER_KEYWORDS = ("status", "สถานะ")


def extract_job_number(message: str) -> Optional[str]:
    match = re.search(r"\b\d+\b", message)
    return match.group(0) if match else None


def is_tracking_request(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in TRACKING_KEYWORDS)


def get_tracking_prompt() -> str:
    return TRACKING_PROMPT


def _candidate_csv_paths() -> list[Path]:
    configured_path = os.environ.get("TRACKING_CSV_PATH", "20260203_LISTJOB_DETEAIL.csv")
    project_root = Path(__file__).resolve().parent.parent
    return [
        Path(configured_path),
        project_root / configured_path,
        project_root / "backend" / configured_path,
    ]


def _normalize_header(header: str) -> str:
    return (header or "").strip().lower().replace(" ", "")


def _excel_column_name(index: int) -> str:
    index += 1
    name = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _find_agent_for_column(headers: list[str], row: list[str], match_index: int) -> tuple[str, int | None]:
    if match_index + 1 < len(headers):
        value = row[match_index + 1].strip() if match_index + 1 < len(row) else ""
        return value, match_index + 1

    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        if any(keyword in normalized for keyword in AGENT_HEADER_KEYWORDS):
            value = row[index].strip() if index < len(row) else ""
            if value:
                return value, index
    return "", None


def _find_status_for_row(headers: list[str], row: list[str]) -> str:
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        if any(keyword in normalized for keyword in STATUS_HEADER_KEYWORDS):
            value = row[index].strip() if index < len(row) else ""
            if value:
                return value
    return ""


def _parse_tracking_rows(rows: list[list[str]], job_number: str, source: str) -> Optional[dict]:
    if len(rows) < 2:
        return None

    headers = [header.strip() for header in rows[0]]
    for row in rows[1:]:
        if not row:
            continue

        for index, header in enumerate(headers):
            normalized = _normalize_header(header)
            if not any(keyword in normalized for keyword in TRACKING_HEADER_KEYWORDS):
                continue

            value = row[index].strip() if index < len(row) else ""
            if value != job_number:
                continue

            agent, agent_index = _find_agent_for_column(headers, row, index)
            return {
                "job_id": value,
                "carrier": agent or "ไม่ระบุ Agent",
                "status": _find_status_for_row(headers, row) or "ไม่ระบุสถานะ",
                "source": source,
                "matched_column": _excel_column_name(index),
                "agent_column": _excel_column_name(agent_index) if agent_index is not None else "",
            }

    return None


def search_local_tracking(job_number: str) -> Optional[dict]:
    for candidate in _candidate_csv_paths():
        if not candidate.exists():
            continue
        try:
            with candidate.open(mode="r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle))
            tracking_data = _parse_tracking_rows(rows, job_number, "Internal CSV")
            if tracking_data:
                return tracking_data
        except Exception as exc:
            print(f"Error reading tracking CSV {candidate}: {exc}")
    return None


async def search_gsheet_tracking(job_number: str) -> Optional[dict]:
    tracking_sheet_id = os.environ.get("TRACKING_SHEET_ID", "15C1B3WWEUPJEO9EhG6L-XNHjxkjCJKrbCvKh7DyvA0I")
    if not tracking_sheet_id:
        return None

    try:
        service = get_sheets_service()
        spreadsheet = service.spreadsheets().get(spreadsheetId=tracking_sheet_id).execute()
        for sheet in spreadsheet.get("sheets", []):
            title = sheet["properties"]["title"]
            values = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=tracking_sheet_id, range=f"'{title}'!A:Z")
                .execute()
                .get("values", [])
            )
            tracking_data = _parse_tracking_rows(values, job_number, f"Google Sheet ({title})")
            if tracking_data:
                return tracking_data
    except Exception as exc:
        print(f"[Tracking Sheet API] Error: {exc}")

    url = f"https://docs.google.com/spreadsheets/d/{tracking_sheet_id}/export?format=csv"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except Exception as exc:
            print(f"[Tracking Sheet] Error: {exc}")
            return None

    rows = list(csv.reader(io.StringIO(response.text)))
    return _parse_tracking_rows(rows, job_number, "Google Sheet")


async def lookup_tracking(job_number: str) -> Optional[dict]:
    return search_local_tracking(job_number) or await search_gsheet_tracking(job_number)


def _carrier_tracking_link(agent_info: str, job_id: str) -> str:
    normalized = (agent_info or "").strip().upper()
    if "DHL" in normalized:
        return f"https://ecommerceportal.dhl.com/track/pages/customer/trackItNowPublic.xhtml?ref={job_id}"
    if "SCG" in normalized:
        return f"{PUBLIC_SITE_BASE_URL}/scg-tracking.html?track={job_id}"
    if "PORLOR" in normalized or "PORLAR" in normalized or "POLOR" in normalized:
        return f"{PUBLIC_SITE_BASE_URL}/porlor-tracking.html?track={job_id}"
    return f"https://track.skyfrog.net/h1IZM?TrackNo={job_id}"


def format_tracking_response(tracking_data: dict) -> str:
    job_id = tracking_data.get("job_id", "-")
    agent_info = tracking_data.get("carrier") or "ไม่ระบุ Agent"
    tracking_link = _carrier_tracking_link(agent_info, job_id)
    return (
        f"DO {job_id} ไปกับขนส่ง {agent_info} งับ\n"
        f"สามารถเช็ค สถานะ ที่ลิ้ง {tracking_link} ได้เลยงับ"
    )


async def build_tracking_context(job_number: str) -> str:
    tracking_data = await lookup_tracking(job_number)
    if not tracking_data:
        return f"[SYSTEM DATA: ไม่พบข้อมูลเลขที่ {job_number} ในระบบติดตาม]"

    agent_info = tracking_data.get("carrier") or "ไม่ระบุ Agent"
    return f"[SYSTEM DATA: เลขที่ {job_number}, Agent ขนส่ง={agent_info}]"
