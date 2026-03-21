import os
import google.generativeai as genai
from supabase import create_client
from sanitizer import sanitize_sheet_content

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def embed_query(text: str) -> list[float]:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text
    )
    return result["embedding"]

def search_knowledge(
    query: str,
    top_k: int = 3,
    threshold: float = 0.65
) -> list[dict]:
    """Embed query, run cosine similarity search, return top_k results."""
    supabase = get_supabase_client()
    if not supabase:
        return [] # ข้ามการค้นหาถ้ายังไม่ได้ตั้งค่า Supabase
        
    try:
        embedding = embed_query(query)
        result = supabase.rpc("match_knowledge", {
            "query_embedding": embedding,
            "match_count": top_k,
            "match_threshold": threshold,
        }).execute()
        
        rows = result.data or []
        
        # Sanitize content before injecting into prompt
        for row in rows:
            row["answer"] = sanitize_sheet_content(row.get("answer", ""))
            row["question"] = sanitize_sheet_content(row.get("question", ""))
            
        return rows
    except Exception as e:
        print(f"Vector search error: {e}")
        return []
