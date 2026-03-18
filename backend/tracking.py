import csv
import io
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv


load_dotenv()

TRACKING_KEYWORDS = (
    "ติดตาม",
    "สถานะ",
    "เลขพัสดุ",
    "เลขงาน",
    "เลขเอกสาร",
    "track",
    "tracking",
    "delivery",
    "job status",
    "job no",
)
TRACKING_PROMPT = (
    "หากต้องการติดตามสถานะ กรุณาส่งเลข delivery, เลขที่เอกสาร หรือ Track_ID ที่เป็นเลข 10 หลักให้ฉันได้เลยครับ"
)

TRACKING_HEADER_KEYWORDS = ("delivery", "jobno", "track", "เลขที่เอกสาร", "หมายเลขใบงาน")
AGENT_HEADER_KEYWORDS = ("agent", "carrier", "ขนส่ง")
STATUS_HEADER_KEYWORDS = ("status", "สถานะ")


def extract_job_number(message: str) -> Optional[str]:
    match = re.search(r"\b\d{10}\b", message)
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


def _find_agent_for_column(headers: list[str], row: list[str], match_index: int) -> str:
    # Prefer the next column when it looks like an Agent/Carrier column.
    if match_index + 1 < len(headers):
        next_header = _normalize_header(headers[match_index + 1])
        if any(keyword in next_header for keyword in AGENT_HEADER_KEYWORDS):
            return row[match_index + 1].strip()

    # Fallback: search same row for any agent/carrier column with a value.
    for index, header in enumerate(headers):
        normalized = _normalize_header(header)
        if any(keyword in normalized for keyword in AGENT_HEADER_KEYWORDS):
            value = row[index].strip() if index < len(row) else ""
            if value:
                return value
    return ""


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

            agent = _find_agent_for_column(headers, row, index) or "ไม่ระบุ Agent"
            status = _find_status_for_row(headers, row) or "ไม่ระบุสถานะ"
            return {
                "job_id": value,
                "carrier": agent,
                "status": status,
                "source": source,
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


async def get_dhl_status(job_number: str) -> str:
    return f"DHL Express: ใบงาน {job_number} อยู่ในขั้นตอนคัดแยกสินค้า (Bangkok Hub)"


async def get_scg_status(job_number: str) -> str:
    return f"SCG Express: ใบงาน {job_number} รถมารับพัสดุแล้ว"


async def get_polar_status(job_number: str) -> str:
    return f"Polar: ใบงาน {job_number} กำลังนำจ่ายพัสดุ"


async def get_skyfrog_status(job_number: str) -> str:
    return f"Skyfrog: ใบงาน {job_number} สถานะ Delivery Planned"


async def fetch_partner_tracking(job_number: str, carrier_hint: str = "") -> str:
    hint = carrier_hint.upper()
    if "DHL" in hint:
        return await get_dhl_status(job_number)
    if "SCG" in hint:
        return await get_scg_status(job_number)
    if "POLAR" in hint:
        return await get_polar_status(job_number)
    return await get_skyfrog_status(job_number)


async def lookup_tracking(job_number: str) -> Optional[dict]:
    return search_local_tracking(job_number) or await search_gsheet_tracking(job_number)


def format_tracking_response(tracking_data: dict) -> str:
    job_id = tracking_data.get("job_id", "-")
    agent_info = tracking_data.get("carrier") or "ไม่ระบุ Agent"
    status_info = tracking_data.get("status") or "ไม่ระบุสถานะ"
    source = tracking_data.get("source", "Internal")
    return (
        f"พบข้อมูลเลขที่ {job_id}\n"
        f"ขนส่ง: {agent_info}\n"
        f"สถานะ: {status_info}\n"
        f"แหล่งข้อมูล: {source}"
    )


async def build_tracking_context(job_number: str) -> str:
    tracking_data = await lookup_tracking(job_number)
    if not tracking_data:
        return f"[SYSTEM DATA: ไม่พบข้อมูลเลขที่ {job_number} ในระบบติดตาม]"

    agent_info = tracking_data.get("carrier") or "ไม่ระบุ Agent"
    status_info = tracking_data.get("status") or "ไม่ระบุสถานะ"
    source = tracking_data.get("source", "Internal")

    if source == "Google Sheet":
        return (
            f"[SYSTEM DATA: ข้อมูลจาก Google Sheet - เลขที่ {job_number}, "
            f"Agent ขนส่ง={agent_info}, สถานะ={status_info}]"
        )

    if job_number.startswith("131"):
        partner_status = await fetch_partner_tracking(job_number, agent_info)
        return (
            f"[SYSTEM DATA: เลขที่ {job_number}, สถานะ SiS={status_info}, "
            f"ข้อมูล Partner={partner_status}]"
        )

    return f"[SYSTEM DATA: เลขที่ {job_number}, Agent ขนส่ง={agent_info}, สถานะ={status_info}]"
