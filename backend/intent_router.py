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


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    normalized = text.strip().lower()
    return any(phrase in normalized for phrase in phrases)


STRONG_SOLAR_KEYWORDS = (
    "solar",
    "solar hub",
    "ส่ง solar",
    "บริการ solar",
    "โซลาร์",
    "แผงโซลาร์",
    "แผง solar",
    "hub em",
    "อินเวอร์เตอร์",
    "inverter",
)

STRONG_BOOKING_KEYWORDS = (
    "จองรถ",
    "จองส่ง",
    "จองขนส่ง",
    "เหมาคัน",
    "รถใหญ่",
    "รับสินค้า",
    "เข้ารับ",
    "pickup",
    "pick up",
    "รถ 4 ล้อ",
    "รถ 6 ล้อ",
    "รถ 10 ล้อ",
    "เทรลเลอร์",
)

STRONG_PRICING_KEYWORDS = (
    "ราคา",
    "ค่าขนส่ง",
    "ค่าส่ง",
    "คิดราคา",
    "ประเมินราคา",
    "quotation",
    "quote",
    "rate",
    "กี่บาท",
    "ราคาเท่าไหร่",
)

STRONG_CLAIM_KEYWORDS = (
    "เคลม",
    "เสียหาย",
    "ชำรุด",
    "ร้องเรียน",
    "ปัญหา",
    "claim",
    "complaint",
    "แตก",
    "บุบ",
    "ของหาย",
    "สูญหาย",
    "ส่งผิด",
    "ผิดพลาด",
)

STRONG_COVERAGE_KEYWORDS = (
    "ทั่วประเทศ",
    "ส่งได้ทั่วประเทศ",
    "ส่งต่างจังหวัด",
    "ส่งไปต่างจังหวัด",
    "ส่งได้ไหม",
    "พื้นที่บริการ",
    "เขตบริการ",
    "ปลายทาง",
    "จังหวัด",
    "coverage",
    "service area",
)

STRONG_DOCUMENT_KEYWORDS = (
    "เอกสาร",
    "ใช้เอกสารอะไร",
    "ใบกำกับ",
    "ใบเสร็จ",
    "invoice",
    "packing list",
    "pod",
)

STRONG_TIMELINE_KEYWORDS = (
    "กี่วัน",
    "ใช้เวลากี่วัน",
    "กี่ชั่วโมง",
    "ตัดรอบ",
    "วันส่ง",
    "วันรับ",
    "ระยะเวลา",
    "timeline",
    "sla",
)


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
    "โซล่า",
    "panel",
    "solar panel",
    "inverter",
    "หลังคา",
    "คลัง solar",
)

BOOKING_KEYWORDS = (
    "จอง",
    "booking",
    "เหมาคัน",
    "รถใหญ่",
    "รับสินค้า",
    "รถไปรับ",
    "เข้ารับ",
    "pickup",
    "pick up",
    "จองรถ",
    "ขนย้าย",
    "ขนส่งด่วน",
    "รถ 4 ล้อ",
    "รถ 6 ล้อ",
    "รถ 10 ล้อ",
    "เทรลเลอร์",
)

PRICING_KEYWORDS = (
    "ราคา",
    "ค่าขนส่ง",
    "ค่าส่ง",
    "คิดราคา",
    "ประเมินราคา",
    "quotation",
    "quote",
    "เรท",
    "rate",
    "ราคาเท่าไหร่",
    "กี่บาท",
    "ค่าบริการ",
    "minimum charge",
)

CLAIM_KEYWORDS = (
    "เคลม",
    "เสียหาย",
    "ชำรุด",
    "ร้องเรียน",
    "ปัญหา",
    "claim",
    "complaint",
    "แตก",
    "บุบ",
    "สูญหาย",
    "ของหาย",
    "ส่งผิด",
    "ผิดพลาด",
    "ล่าช้า",
    "ช้า",
)

HUMAN_KEYWORDS = (
    "ติดต่อเจ้าหน้าที่",
    "คุยกับคน",
    "human",
    "agent",
    "แอดมิน",
    "ขอคุยคน",
    "พนักงาน",
    "เจ้าหน้าที่",
    "คนจริง",
)

COVERAGE_KEYWORDS = (
    "พื้นที่",
    "จังหวัด",
    "ปลายทาง",
    "ส่งได้ไหม",
    "ส่งไปได้ไหม",
    "coverage",
    "service area",
    "เขตบริการ",
    "ทั่วประเทศ",
)

DOCUMENT_KEYWORDS = (
    "เอกสาร",
    "ใช้เอกสารอะไร",
    "ใบกำกับ",
    "ใบเสร็จ",
    "เอกสารประกอบ",
    "invoice",
    "packing list",
    "pod",
)

TIME_KEYWORDS = (
    "กี่วัน",
    "ใช้เวลากี่วัน",
    "กี่ชั่วโมง",
    "ตัดรอบ",
    "เข้ารับกี่โมง",
    "วันส่ง",
    "วันรับ",
    "ระยะเวลา",
    "timeline",
    "sla",
)


def classify_intent(message: str) -> ChatIntent:
    raw_text = message.strip()
    lowered = raw_text.lower()
    token_count = len(raw_text.split())
    is_long_form = len(raw_text) >= 120 or token_count >= 24

    if _contains_phrase(lowered, STRONG_SOLAR_KEYWORDS):
        return ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query=(
                f"บริการส่ง Solar ผ่าน Hub, แผงโซลาร์, วิธีใช้งาน, เงื่อนไข, "
                f"ข้อจำกัด, ขั้นตอน, ประเมินงาน, {raw_text}"
            ),
            top_k=6,
            threshold=0.52,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain what the Solar Hub service is, who it suits, the constraints, and the next step."
            ),
        )

    if _contains_phrase(lowered, STRONG_BOOKING_KEYWORDS):
        return ChatIntent(
            name="booking",
            lane="hybrid",
            knowledge_query=(
                f"การจองขนส่งสินค้า เหมาคัน รถใหญ่ เข้ารับสินค้า pickup "
                f"ข้อมูลที่ต้องใช้ ขั้นตอนการจอง SLA เอกสาร {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on booking steps, what information is needed, service scope, and recommended next steps."
            ),
        )

    if _contains_phrase(lowered, STRONG_PRICING_KEYWORDS):
        return ChatIntent(
            name="pricing",
            lane="hybrid",
            knowledge_query=(
                f"ราคา ค่าขนส่ง quotation rate ปัจจัยการคิดราคา "
                f"น้ำหนัก ขนาด ระยะทาง พื้นที่บริการ ขั้นต่ำ {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain price factors clearly and say what input data is still needed for an exact quote."
            ),
        )

    if _contains_phrase(lowered, STRONG_CLAIM_KEYWORDS):
        return ChatIntent(
            name="claim",
            lane="hybrid",
            knowledge_query=(
                f"การเคลมสินค้าเสียหาย สินค้าชำรุด ของหาย ส่งผิด "
                f"ร้องเรียน ปัญหาการขนส่ง ขั้นตอน เอกสาร รูปถ่าย ระยะเวลาตรวจสอบ {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Guide the user step by step through claims or issue reporting and list the needed evidence."
            ),
        )

    if _contains_phrase(lowered, STRONG_COVERAGE_KEYWORDS):
        return ChatIntent(
            name="coverage",
            lane="hybrid",
            knowledge_query=(
                f"พื้นที่ให้บริการ จังหวัดปลายทาง coverage service area เขตบริการ "
                f"ส่งได้ทั่วประเทศ ส่งต่างจังหวัด {raw_text}"
            ),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on service coverage, destination eligibility, and next best steps when uncertain."
            ),
        )

    if _contains_phrase(lowered, STRONG_DOCUMENT_KEYWORDS):
        return ChatIntent(
            name="document",
            lane="hybrid",
            knowledge_query=(
                f"เอกสารที่ใช้ เอกสารประกอบ invoice packing list POD ใบกำกับ {raw_text}"
            ),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain required documents clearly and distinguish required vs optional paperwork."
            ),
        )

    if _contains_phrase(lowered, STRONG_TIMELINE_KEYWORDS):
        return ChatIntent(
            name="timeline",
            lane="hybrid",
            knowledge_query=(
                f"ระยะเวลาขนส่ง SLA ตัดรอบ เข้ารับสินค้า วันส่ง วันถึง timeline {raw_text}"
            ),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Clarify timing expectations and highlight what can affect the timeline."
            ),
        )

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
            knowledge_query=(
                f"บริการส่ง Solar ผ่าน Hub, แผงโซลาร์, เงื่อนไข, วิธีใช้งาน, "
                f"ขนาดงาน, ข้อจำกัด, ราคาเบื้องต้น, ขั้นตอน, {raw_text}"
            ),
            top_k=6,
            threshold=0.52,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain what the Solar Hub service is, who it suits, the constraints, and the next step."
            ),
        )

    if _contains_any(lowered, BOOKING_KEYWORDS):
        return ChatIntent(
            name="booking",
            lane="hybrid",
            knowledge_query=(
                f"การจองขนส่งสินค้า เหมาคัน รถใหญ่ เข้ารับสินค้า pickup "
                f"ข้อมูลที่ต้องใช้ ขั้นตอนการจอง SLA เอกสาร {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on booking steps, what information is needed, service scope, and recommended next steps."
            ),
        )

    if _contains_any(lowered, PRICING_KEYWORDS):
        return ChatIntent(
            name="pricing",
            lane="hybrid",
            knowledge_query=(
                f"ราคา ค่าขนส่ง quotation rate ปัจจัยการคิดราคา "
                f"น้ำหนัก ขนาด ระยะทาง พื้นที่บริการ ขั้นต่ำ {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain price factors clearly and say what input data is still needed for an exact quote."
            ),
        )

    if _contains_any(lowered, CLAIM_KEYWORDS):
        return ChatIntent(
            name="claim",
            lane="hybrid",
            knowledge_query=(
                f"การเคลมสินค้าเสียหาย สินค้าชำรุด ของหาย ส่งผิด "
                f"ร้องเรียน ปัญหาการขนส่ง ขั้นตอน เอกสาร รูปถ่าย ระยะเวลาตรวจสอบ {raw_text}"
            ),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Guide the user step by step through claims or issue reporting and list the needed evidence."
            ),
        )

    if _contains_any(lowered, COVERAGE_KEYWORDS):
        return ChatIntent(
            name="coverage",
            lane="hybrid",
            knowledge_query=f"พื้นที่ให้บริการ จังหวัดปลายทาง coverage service area เขตบริการ {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on service coverage, destination eligibility, and next best steps when uncertain."
            ),
        )

    if _contains_any(lowered, DOCUMENT_KEYWORDS):
        return ChatIntent(
            name="document",
            lane="hybrid",
            knowledge_query=f"เอกสารที่ใช้ เอกสารประกอบ invoice packing list POD ใบกำกับ {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain required documents clearly and distinguish required vs optional paperwork."
            ),
        )

    if _contains_any(lowered, TIME_KEYWORDS):
        return ChatIntent(
            name="timeline",
            lane="hybrid",
            knowledge_query=f"ระยะเวลาขนส่ง SLA ตัดรอบ เข้ารับสินค้า วันส่ง วันถึง timeline {raw_text}",
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Clarify timing expectations and highlight what can affect the timeline."
            ),
        )

    if is_long_form:
        return ChatIntent(
            name="longform_consult",
            lane="longform",
            knowledge_query=(
                f"บริบทลูกค้า เคสขนส่งยาว หลายเงื่อนไข คำแนะนำการเลือกบริการ "
                f"สรุปสถานการณ์และคำตอบที่เหมาะสม {raw_text}"
            ),
            top_k=6,
            threshold=0.50,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "For long questions, summarize the situation first, then give practical recommendations and a next step."
            ),
        )

    return ChatIntent(
        name="general_chat",
        lane="general",
        knowledge_query=f"บริการ SiS Freight คำถามทั่วไป {raw_text}",
        top_k=3,
        threshold=0.60,
        system_hint=(
            "Respond naturally in Thai as Nong Godang. "
            "Be warm, concise, and helpful. If unsure, be honest and suggest the next best step."
        ),
    )
