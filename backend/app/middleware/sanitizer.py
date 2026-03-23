import re


DIRECT_INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions",
    r"(you are now|pretend to be|act as|forget everything)",
    r"system\s*prompt",
    r"jailbreak",
    r"disregard (your|all|previous)",
]

INDIRECT_INJECTION_PATTERNS = [
    r"<[a-z]+.*?>",
    r"\{\{.*?\}\}",
    r"\\n\\n(human|assistant):",
]


def is_user_injection(text: str) -> bool:
    for pattern in DIRECT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def sanitize_sheet_content(text: str) -> str:
    """Clean content fetched from Sheets before injecting it into prompts."""
    if not text:
        return ""

    for pattern in INDIRECT_INJECTION_PATTERNS + DIRECT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return "[Content flagged by safety filter]"

    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:2000]


def validate_message(message: str) -> tuple[bool, str]:
    if not message or not message.strip():
        return False, "Empty message"
    if len(message) > 1000:
        return False, "Message too long (max 1000 chars)"
    if is_user_injection(message):
        return False, "Message blocked by safety filter"
    return True, ""


__all__ = [
    "DIRECT_INJECTION_PATTERNS",
    "INDIRECT_INJECTION_PATTERNS",
    "is_user_injection",
    "sanitize_sheet_content",
    "validate_message",
]
