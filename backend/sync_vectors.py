from .app.services.knowledge_sync_core import (
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    SHEET_ID,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
    embed_text,
    sync,
)

__all__ = [
    "EMBEDDING_MODEL",
    "GEMINI_API_KEY",
    "SHEET_ID",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_URL",
    "embed_text",
    "sync",
]


if __name__ == "__main__":
    sync()
