import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
REQUIRED_HEADERS = {"question", "answer"}


def _load_credentials():
    raw_credentials = os.environ.get("GOOGLE_CREDENTIALS", "").strip()
    if not raw_credentials:
        raise ValueError("Missing GOOGLE_CREDENTIALS environment variable")

    credentials_info = json.loads(raw_credentials)
    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=SCOPES,
    )


def get_sheets_service():
    credentials = _load_credentials()
    return build("sheets", "v4", credentials=credentials)


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
