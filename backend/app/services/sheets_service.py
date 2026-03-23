from __future__ import annotations

from .sheets_core import append_knowledge_row, get_sheet_tab_link, knowledge_row_exists


class SheetsService:
    append_row = staticmethod(append_knowledge_row)
    get_tab_link = staticmethod(get_sheet_tab_link)
    row_exists = staticmethod(knowledge_row_exists)
