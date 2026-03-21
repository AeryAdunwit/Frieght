import os
from functools import lru_cache
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from supabase import Client, create_client

from .app.logging_utils import get_logger, log_with_context
from .sanitizer import sanitize_sheet_content


load_dotenv()

EMBEDDING_CACHE_SIZE = int(os.environ.get("EMBEDDING_CACHE_SIZE", "256"))
KNOWLEDGE_QUERY_CACHE_SIZE = int(os.environ.get("KNOWLEDGE_QUERY_CACHE_SIZE", "256"))
TOPIC_ROWS_CACHE_SIZE = int(os.environ.get("TOPIC_ROWS_CACHE_SIZE", "64"))
logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client | None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def _normalize_query_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def _sanitize_result_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized_rows: list[dict[str, Any]] = []
    for row in rows:
        sanitized_rows.append(
            {
                **row,
                "question": sanitize_sheet_content(row.get("question", "")),
                "answer": sanitize_sheet_content(row.get("answer", "")),
                "keywords": sanitize_sheet_content(row.get("keywords", "")),
                "intent": sanitize_sheet_content(row.get("intent", "")),
                "content": sanitize_sheet_content(row.get("content", "")),
            }
        )
    return sanitized_rows


def _clone_rows(rows: tuple[dict[str, Any], ...] | list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


@lru_cache(maxsize=EMBEDDING_CACHE_SIZE)
def _cached_embed_query(text: str, embedding_model: str) -> tuple[float, ...]:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    result = genai.embed_content(
        model=embedding_model,
        content=text,
        output_dimensionality=768,
    )
    return tuple(result["embedding"])


def embed_query(text: str) -> list[float]:
    embedding_model = os.environ.get("EMBEDDING_MODEL", "models/gemini-embedding-001")
    normalized_text = _normalize_query_text(text)
    return list(_cached_embed_query(normalized_text, embedding_model))


@lru_cache(maxsize=KNOWLEDGE_QUERY_CACHE_SIZE)
def _cached_search_knowledge(query: str, top_k: int, threshold: float) -> tuple[dict[str, Any], ...]:
    supabase = get_supabase_client()
    if not supabase or not query:
        return tuple()

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

        rows = _sanitize_result_rows(result.data or [])
        return tuple(rows)
    except Exception as exc:
        log_with_context(logger, 40, "Vector search failed", query=query, top_k=top_k, threshold=threshold, error=exc)
        return tuple()


def search_knowledge(query: str, top_k: int = 3, threshold: float = 0.65) -> list[dict]:
    normalized_query = _normalize_query_text(query)
    if not normalized_query:
        return []

    cached_rows = _cached_search_knowledge(normalized_query, int(top_k), float(threshold))
    return _clone_rows(cached_rows)


@lru_cache(maxsize=TOPIC_ROWS_CACHE_SIZE)
def _cached_topic_rows(topic: str, limit: int) -> tuple[dict[str, Any], ...]:
    supabase = get_supabase_client()
    if not supabase or not topic:
        return tuple()

    try:
        try:
            result = (
                supabase.table("knowledge_base")
                .select("topic,question,answer,keywords,intent,content")
                .eq("topic", topic)
                .limit(limit)
                .execute()
            )
        except Exception:
            result = (
                supabase.table("knowledge_base")
                .select("topic,question,answer,intent,content")
                .eq("topic", topic)
                .limit(limit)
                .execute()
            )
        rows = _sanitize_result_rows(result.data or [])
        return tuple(rows)
    except Exception as exc:
        log_with_context(logger, 40, "Topic row load failed", topic=topic, limit=limit, error=exc)
        return tuple()


def load_topic_rows(topic: str, limit: int = 200) -> list[dict]:
    normalized_topic = _normalize_query_text(topic)
    if not normalized_topic:
        return []
    cached_rows = _cached_topic_rows(normalized_topic, int(limit))
    return _clone_rows(cached_rows)


def invalidate_knowledge_caches() -> None:
    _cached_embed_query.cache_clear()
    _cached_search_knowledge.cache_clear()
    _cached_topic_rows.cache_clear()
