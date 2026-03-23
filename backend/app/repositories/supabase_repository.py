from __future__ import annotations

from ..services.vector_search_core import get_supabase_client


class SupabaseRepository:
    def get_client(self):
        return get_supabase_client()

    def is_configured(self) -> bool:
        return self.get_client() is not None
