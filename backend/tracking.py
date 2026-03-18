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


def search_local_tracking(job_number: str) -> Optional[dict]:
    for candidate in _candidate_csv_paths():
        if not candidate.exists():
            continue
        try:
            with candidate.open(mode="r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    target = (
                        row.get("หมายเลขใบงาน")
                        or row.get("JobNo")
                        or row.get("Delivery")
                        or row.get("เลขที่เอกสาร")
                        or row.get("Track_ID")
                        or ""
                    ).strip()
                    if target == job_number:
                        return {
                            "job_id": target,
                            "status": (row.get("สถานะ") or row.get("JobStatus") or "").strip(),
                            "carrier": (row.get("ShortName") or row.get("Carrier") or "").strip(),
                            "customer": (row.get("CustomerName") or "").strip(),
                            "source": "Internal CSV",
                        }
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

    reader = csv.DictReader(io.StringIO(response.text))
    reader.fieldnames = [name.strip() for name in reader.fieldnames] if reader.fieldnames else []
    for row in reader:
        target = (
            row.get("หมายเลขใบงาน")
            or row.get("JobNo")
            or row.get("Delivery")
            or row.get("เลขที่เอกสาร")
            or row.get("Track_ID")
            or ""
        ).strip()
        if target == job_number:
            return {
                "job_id": target,
                "carrier": (
                    row.get("Agent ขนส่ง")
                    or row.get("Agent")
                    or row.get("ขนส่ง")
                    or row.get("Carrier")
                    or "ไม่ระบุ Agent"
                ).strip(),
                "status": (row.get("สถานะ") or row.get("JobStatus") or "ไม่ระบุสถานะ").strip(),
                "source": "Google Sheet",
            }
    return None


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
