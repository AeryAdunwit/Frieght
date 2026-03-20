import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build


READ_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
WRITE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
REQUIRED_HEADERS = {"question", "answer"}
DEFAULT_HEADERS = ["question", "answer", "keywords", "intent", "active"]


def _load_credentials(scopes: list[str] | None = None):
    raw_credentials = os.environ.get("GOOGLE_CREDENTIALS", "").strip()
    if not raw_credentials:
        raise ValueError("Missing GOOGLE_CREDENTIALS environment variable")

    credentials_info = json.loads(raw_credentials)
    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=scopes or READ_SCOPES,
    )


def get_sheets_service():
    credentials = _load_credentials(READ_SCOPES)
    return build("sheets", "v4", credentials=credentials)


def get_write_sheets_service():
    credentials = _load_credentials(WRITE_SCOPES)
    return build("sheets", "v4", credentials=credentials)


def _ensure_sheet_exists(service, sheet_id: str, topic: str) -> None:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_titles = {
        sheet["properties"]["title"]
        for sheet in spreadsheet.get("sheets", [])
    }
    if topic in existing_titles:
        return

    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": topic}}}]},
    ).execute()


def _ensure_sheet_headers(service, sheet_id: str, topic: str) -> None:
    values = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range=f"'{topic}'!A1:E1")
        .execute()
        .get("values", [])
    )
    headers = values[0] if values else []
    normalized_headers = [str(header).strip().lower() for header in headers]
    if normalized_headers[: len(DEFAULT_HEADERS)] == DEFAULT_HEADERS:
        return

    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{topic}'!A1:E1",
        valueInputOption="RAW",
        body={"values": [DEFAULT_HEADERS]},
    ).execute()


def append_knowledge_row(
    sheet_id: str,
    topic: str,
    *,
    question: str,
    answer: str,
    keywords: str = "",
    intent: str = "",
    active: str = "yes",
) -> dict:
    if not sheet_id:
        raise ValueError("Missing SHEET_ID environment variable")

    safe_topic = (topic or "").strip()
    if not safe_topic:
        raise ValueError("Missing topic for Google Sheet append")

    service = get_write_sheets_service()
    _ensure_sheet_exists(service, sheet_id, safe_topic)
    _ensure_sheet_headers(service, sheet_id, safe_topic)

    values = [[question.strip(), answer.strip(), keywords.strip(), intent.strip(), (active or "yes").strip() or "yes"]]
    return (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=sheet_id,
            range=f"'{safe_topic}'!A:E",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        )
        .execute()
    )


def load_knowledge_rows(sheet_id: str) -> list[dict]:
    if not sheet_id:
        raise ValueError("Missing SHEET_ID environment variable")

    service = get_sheets_service()
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()

    rows: list[dict] = []
    for sheet in spreadsheet.get("sheets", []):
        topic = sheet["properties"]["title"]
        values = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=f"'{topic}'!A:Z")
            .execute()
            .get("values", [])
        )

        if len(values) < 2:
            continue

        headers = [header.lower().strip() for header in values[0]]
        if not REQUIRED_HEADERS.issubset(set(headers)):
            continue

        for row_index, row_values in enumerate(values[1:], start=1):
            entry = {
                "topic": topic,
                "row_index": row_index,
                "question": "",
                "answer": "",
                "keywords": "",
                "intent": "",
                "active": "",
            }
            for column_index, header in enumerate(headers):
                entry[header] = row_values[column_index].strip() if column_index < len(row_values) else ""

            if entry.get("active", "").strip().lower() == "no":
                continue

            if entry["question"] and entry["answer"]:
                rows.append(entry)

    return rows
