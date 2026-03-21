import os
import time

import google.generativeai as genai
from dotenv import load_dotenv
from supabase import create_client

from .app.logging_utils import get_logger, log_with_context
from .sheets_loader import load_knowledge_rows


load_dotenv()

SHEET_ID = os.environ.get("SHEET_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")
logger = get_logger(__name__)


def embed_text(text: str) -> list[float]:
    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        output_dimensionality=768,
    )
    time.sleep(0.05)
    return result["embedding"]


def sync() -> dict[str, int]:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Missing Supabase configuration for sync")
    if not GEMINI_API_KEY:
        raise RuntimeError("Missing GEMINI_API_KEY for sync")

    rows = load_knowledge_rows(SHEET_ID)
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    log_with_context(logger, 20, "Knowledge sync started", rows=len(rows))
    failed_rows = 0

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
                "keywords": row.get("keywords", ""),
                "intent": intent,
                "content": content,
                "embedding": embed_text(content),
            }
            supabase.table("knowledge_base").upsert(payload).execute()
        except Exception as exc:
            failed_rows += 1
            log_with_context(
                logger,
                40,
                "Knowledge row sync failed",
                topic=row.get("topic"),
                row_index=row.get("row_index"),
                error=exc,
            )

    log_with_context(logger, 20, "Knowledge sync finished", rows=len(rows), failed_rows=failed_rows)
    return {
        "rows_synced": len(rows),
        "failed_rows": failed_rows,
    }


if __name__ == "__main__":
    sync()
