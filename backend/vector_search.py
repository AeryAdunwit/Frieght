import os
from functools import lru_cache

import google.generativeai as genai
from dotenv import load_dotenv
from supabase import Client, create_client

from .sanitizer import sanitize_sheet_content


load_dotenv()


@lru_cache(maxsize=1)
def get_supabase_client() -> Client | None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def embed_query(text: str) -> list[float]:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    embedding_model = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")
    result = genai.embed_content(
        model=embedding_model,
        content=text,
        output_dimensionality=768,
    )
    return result["embedding"]


def search_knowledge(query: str, top_k: int = 3, threshold: float = 0.65) -> list[dict]:
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        embedding = embed_query(query)
        result = supabase.rpc(
            "match_knowledge",
            {
                "query_embedding": embedding,
                "match_count": top_k,
                "match_threshold": threshold,
            },
        ).execute()

        rows = result.data or []
        for row in rows:
            row["question"] = sanitize_sheet_content(row.get("question", ""))
            row["answer"] = sanitize_sheet_content(row.get("answer", ""))

        return rows
    except Exception as exc:
        print(f"Vector search error: {exc}")
        return []
