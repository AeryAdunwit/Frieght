import re

DIRECT_INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions",
    r"(you are now|pretend to be|act as|forget everything)",
    r"system\s*prompt",
    r"jailbreak",
    r"disregard (your|all|previous)",
]

INDIRECT_INJECTION_PATTERNS = [
    r"<[a-z]+.*?>",                  # HTML/XML tags
    r"\{\{.*?\}\}",              # Template injection
    r"\\n\\n(human|assistant):", # Prompt format spoofing
]

def is_user_injection(text: str) -> bool:
    for p in DIRECT_INJECTION_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False

def sanitize_sheet_content(text: str) -> str:
    """Clean content fetched from Sheets before injecting into prompt."""
    if not text:
        return ""
    for p in INDIRECT_INJECTION_PATTERNS + DIRECT_INJECTION_PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return "[Content flagged by safety filter]"
    # Strip control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    return text[:2000]  # Hard cap to prevent context overflow

def validate_message(msg: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)."""
    if not msg or not msg.strip():
        return False, "Empty message"
    if len(msg) > 1000:
        return False, "Message too long (max 1000 chars)"
    if is_user_injection(msg):
        return False, "Message blocked by safety filter"
    return True, ''
