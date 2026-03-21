from __future__ import annotations

import re


INTENT_TEXT_REPLACEMENTS = (
    ("×", "x"),
    ("÷", "/"),
    ("ฮับ", "hub"),
    ("โซล่า", "โซลาร์"),
    ("โซลาร์เซลล์", "โซลาร์"),
    ("พ็อด", "pod"),
    ("พอด", "pod"),
    ("คิวเตชั่น", "quotation"),
)


def normalize_intent_message(message: str) -> str:
    normalized = (message or "").strip().lower()
    for source, target in INTENT_TEXT_REPLACEMENTS:
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized
