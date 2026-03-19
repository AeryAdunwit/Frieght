import os
import time

import google.generativeai as genai
from dotenv import load_dotenv
from supabase import create_client

from .sheets_loader import load_knowledge_rows


load_dotenv()

SHEET_ID = os.environ.get("SHEET_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")


def embed_text(text: str) -> list[float]:
    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        output_dimensionality=768,
    )
    time.sleep(0.05)
    return result["embedding"]


def sync() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Missing Supabase configuration for sync")
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY for sync")

    rows = load_knowledge_rows(SHEET_ID)
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print(f"Syncing {len(rows)} rows...")

    for row in rows:
        try:
            intent = (row.get("intent") or "").strip()
            content_parts = [f"Q: {row['question']}", f"A: {row['answer']}"]
            if intent:
                content_parts.append(f"Intent: {intent}")
            if row.get("keywords"):
                content_parts.append(f"Keywords: {row['keywords']}")
            content = "\n".join(content_parts)
            row_id = f"{row['topic']}_{row['row_index']}"
            payload = {
                "id": row_id,
                "topic": row["topic"],
                "question": row["question"],
                "answer": row["answer"],
                "intent": intent,
                "content": content,
                "embedding": embed_text(content),
            }
            supabase.table("knowledge_base").upsert(payload).execute()
        except Exception as exc:
            print(f"Failed to sync row {row.get('topic')}#{row.get('row_index')}: {exc}")

    print(f"Done. {len(rows)} rows synced to Supabase.")


if __name__ == "__main__":
    sync()
