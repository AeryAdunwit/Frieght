from dataclasses import dataclass


@dataclass(frozen=True)
class ChatIntent:
    name: str
    lane: str
    knowledge_query: str
    top_k: int
    threshold: float
    system_hint: str
    canned_response: str = ""


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


GREETING_KEYWORDS = (
    "สวัสดี",
    "หวัดดี",
    "hello",
    "hi ",
    "hi",
    "good morning",
    "good afternoon",
)

THANKS_KEYWORDS = (
    "ขอบคุณ",
    "thank",
    "thx",
    "thanks",
)

SOLAR_KEYWORDS = (
    "solar",
    "โซลาร์",
    "แผง",
    "hub",
    "hub em",
)

BOOKING_KEYWORDS = (
    "จอง",
    "booking",
    "เหมาคัน",
    "รถใหญ่",
    "รับสินค้า",
)

PRICING_KEYWORDS = (
    "ราคา",
    "ค่าขนส่ง",
    "ค่าส่ง",
    "คิดราคา",
    "ประเมินราคา",
    "quotation",
    "quote",
)

CLAIM_KEYWORDS = (
    "เคลม",
    "เสียหาย",
    "ชำรุด",
    "ร้องเรียน",
    "ปัญหา",
    "claim",
    "complaint",
)

HUMAN_KEYWORDS = (
    "ติดต่อเจ้าหน้าที่",
    "คุยกับคน",
    "human",
    "agent",
    "แอดมิน",
)


def classify_intent(message: str) -> ChatIntent:
    raw_text = message.strip()
    lowered = raw_text.lower()
    token_count = len(raw_text.split())
    is_long_form = len(raw_text) >= 120 or token_count >= 24

    if raw_text and len(raw_text) <= 20 and _contains_any(lowered, GREETING_KEYWORDS):
        return ChatIntent(
            name="greeting",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply briefly and warmly as Nong Godang.",
            canned_response="สวัสดีงับ น้องโกดังพร้อมช่วยเรื่องขนส่งและบริการของ SiS Freight น้า",
        )

    if raw_text and len(raw_text) <= 30 and _contains_any(lowered, THANKS_KEYWORDS):
        return ChatIntent(
            name="thanks",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply briefly and warmly as Nong Godang.",
            canned_response="ยินดีงับ ถ้ามีอะไรให้น้องโกดังช่วยต่อ ถามมาได้เลยน้า",
        )

    if _contains_any(lowered, HUMAN_KEYWORDS):
        return ChatIntent(
            name="human_handoff",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply clearly and politely.",
            canned_response="ได้เลยงับ ถ้าต้องการคุยกับเจ้าหน้าที่ แจ้งรายละเอียดที่ต้องการไว้ได้เลย เดี๋ยวน้องโกดังช่วยพาไปต่อให้งับ",
        )

    if _contains_any(lowered, SOLAR_KEYWORDS):
        return ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query=f"บริการส่ง Solar ผ่าน Hub, เงื่อนไข, วิธีใช้งาน, ราคาเบื้องต้น, {raw_text}",
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "When useful, explain what the Solar Hub service is, who it suits, and the next step."
            ),
        )

    if _contains_any(lowered, BOOKING_KEYWORDS):
        return ChatIntent(
            name="booking",
            lane="hybrid",
            knowledge_query=f"การจองขนส่งสินค้า เหมาคัน รถใหญ่ ขั้นตอน เอกสาร {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on booking steps, what information is needed, and recommended next steps."
            ),
        )

    if _contains_any(lowered, PRICING_KEYWORDS):
        return ChatIntent(
            name="pricing",
            lane="hybrid",
            knowledge_query=f"ราคา ค่าขนส่ง เงื่อนไขการคิดราคา quotation {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Be explicit when exact pricing is unavailable and state what info is needed to estimate price."
            ),
        )

    if _contains_any(lowered, CLAIM_KEYWORDS):
        return ChatIntent(
            name="claim",
            lane="hybrid",
            knowledge_query=f"การเคลมสินค้าเสียหาย ร้องเรียน ปัญหาการขนส่ง ขั้นตอน {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Guide the user through claims or issue-reporting steps clearly."
            ),
        )

    if is_long_form:
        return ChatIntent(
            name="longform_consult",
            lane="longform",
            knowledge_query=raw_text,
            top_k=5,
            threshold=0.52,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "For long questions, summarize the situation first, then give practical recommendations."
            ),
        )

    return ChatIntent(
        name="general_chat",
        lane="general",
        knowledge_query=raw_text,
        top_k=3,
        threshold=0.60,
        system_hint=(
            "Respond naturally in Thai as Nong Godang. "
            "Be warm, concise, and helpful. If unsure, be honest and suggest the next best step."
        ),
    )
