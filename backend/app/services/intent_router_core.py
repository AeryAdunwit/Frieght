from dataclasses import dataclass, field

from .intent_quality_service import normalize_intent_message


@dataclass(frozen=True)
class ChatIntent:
    name: str
    lane: str
    knowledge_query: str
    top_k: int
    threshold: float
    system_hint: str
    canned_response: str = ""
    preferred_answer_intent: str = ""
    missing_fields: list[str] = field(default_factory=list)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    normalized = normalize_intent_message(text)
    return any(phrase in normalized for phrase in phrases)


def _detect_solar_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("หนัก", "น้ำหนัก", "กี่กิโล", "กี่ตัน", "kg", "กก", "ตัน")):
        return "weight"
    if any(keyword in normalized for keyword in ("ข้อจำกัด", "เงื่อนไข", "ต้องระวัง", "จำกัด")):
        return "limitations"
    if any(keyword in normalized for keyword in ("ราคา", "ค่าส่ง", "ประเมิน", "quote", "quotation")):
        return "pricing"
    if any(keyword in normalized for keyword in ("เตรียม", "ข้อมูล", "ต้องใช้", "เอกสาร", "แจ้งอะไร")):
        return "required_info"
    if any(keyword in normalized for keyword in ("เหมาะ", "งานแบบไหน", "กรณีไหน", "ใช้กับ")):
        return "fit_use_case"
    return "definition"


def _build_solar_knowledge_query(raw_text: str) -> str:
    subintent = _detect_solar_subintent(raw_text)
    focus_map = {
        "weight": "Solar หนักเท่าไหร่ น้ำหนัก solar กี่กิโล กี่ตัน weight",
        "definition": "บริการส่ง Solar ผ่าน Hub คืออะไร ธุรกิจ em คืออะไร definition",
        "fit_use_case": "งานแบบไหนเหมาะกับ Solar ผ่าน Hub ใช้กรณีไหน fit use case",
        "required_info": "Solar ผ่าน Hub ต้องเตรียมข้อมูลอะไร ต้องแจ้งอะไร required info",
        "pricing": "Solar ผ่าน Hub คิดราคายังไง ราคา solar hub ประเมินราคา pricing",
        "limitations": "Solar Hub มีข้อจำกัดอะไร เงื่อนไขอะไร limitations",
    }
    return f"{focus_map.get(subintent, focus_map['definition'])} {raw_text}".strip()


def _detect_booking_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("ข้อมูล", "ต้องใช้", "แจ้งอะไร", "ใช้อะไร", "เตรียมอะไร")):
        return "booking_input"
    if any(keyword in normalized for keyword in ("ล่วงหน้า", "advance", "ก่อนกี่วัน")):
        return "booking_timing"
    if any(keyword in normalized for keyword in ("เหมาคัน", "รถใหญ่", "หลายจุด", "งานพิเศษ", "เทรลเลอร์")):
        return "special_case"
    return "booking_step"


def _build_booking_knowledge_query(raw_text: str) -> str:
    subintent = _detect_booking_subintent(raw_text)
    focus_map = {
        "booking_step": "ถ้าจะจองงานต้องทำอย่างไร booking step วิธีจอง",
        "booking_input": "ต้องใช้ข้อมูลอะไรในการจอง booking input ต้องแจ้งอะไร",
        "booking_timing": "ควรจองล่วงหน้าไหม booking timing advance",
        "special_case": "งานเหมาคัน รถใหญ่ หลายจุดส่ง ต้องแจ้งอะไร special case",
    }
    return f"{focus_map.get(subintent, focus_map['booking_step'])} {raw_text}".strip()


def _detect_pricing_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("ข้อมูล", "ใช้อะไร", "ส่งอะไร", "quotation", "quote")):
        return "quote_input"
    if any(keyword in normalized for keyword in ("ราคากลาง", "ขั้นต่ำ", "minimum")):
        return "pricing_policy"
    if any(keyword in normalized for keyword in ("หน้างาน", "site", "ประเมินหน้างาน")):
        return "site_check"
    return "pricing_factor"


def _build_pricing_knowledge_query(raw_text: str) -> str:
    subintent = _detect_pricing_subintent(raw_text)
    focus_map = {
        "pricing_factor": "คิดราคาค่าส่งจากอะไรบ้าง pricing factor ค่าส่งคิดจากอะไร",
        "quote_input": "ขอประเมินราคา ต้องส่งข้อมูลอะไรบ้าง quote input quotation",
        "pricing_policy": "มีราคากลางไหม ขั้นต่ำเท่าไหร่ pricing policy",
        "site_check": "งานแบบไหนต้องประเมินหน้างานก่อน site check",
    }
    return f"{focus_map.get(subintent, focus_map['pricing_factor'])} {raw_text}".strip()


def _detect_claim_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("หลักฐาน", "รูป", "เอกสาร", "แนบอะไร")):
        return "claim_evidence"
    if any(keyword in normalized for keyword in ("กี่วัน", "นานไหม", "ใช้เวลา", "timeline")):
        return "claim_timeline"
    if any(keyword in normalized for keyword in ("แจ้งอะไร", "ข้อมูลอะไร", "ต้องส่งอะไร")):
        return "claim_input"
    return "claim_step"


def _build_claim_knowledge_query(raw_text: str) -> str:
    subintent = _detect_claim_subintent(raw_text)
    focus_map = {
        "claim_step": "สินค้าชำรุดต้องทำอย่างไร claim step เคลมยังไง",
        "claim_input": "ของหาย ส่งผิด ต้องแจ้งอะไรบ้าง claim input",
        "claim_evidence": "เคลมต้องใช้หลักฐานอะไร claim evidence",
        "claim_timeline": "ใช้เวลาตรวจสอบประมาณกี่วัน claim timeline",
    }
    return f"{focus_map.get(subintent, focus_map['claim_step'])} {raw_text}".strip()


def _detect_coverage_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("ต่างจังหวัด",)):
        return "upcountry"
    if any(keyword in normalized for keyword in ("พื้นที่พิเศษ", "ห่างไกล", "ต้องเช็กก่อน")):
        return "restricted_area"
    if any(keyword in normalized for keyword in ("ปลายทางยังไม่แน่ใจ", "เช็กปลายทาง", "ตรวจพื้นที่")):
        return "check_area"
    return "nationwide"


def _build_coverage_knowledge_query(raw_text: str) -> str:
    subintent = _detect_coverage_subintent(raw_text)
    focus_map = {
        "nationwide": "ส่งได้ทั่วประเทศไหม coverage nationwide",
        "upcountry": "มีส่งต่างจังหวัดไหม coverage upcountry",
        "restricted_area": "พื้นที่ไหนต้องเช็กก่อน coverage restricted area",
        "check_area": "ปลายทางยังไม่แน่ใจต้องทำอย่างไร coverage check area",
    }
    return f"{focus_map.get(subintent, focus_map['nationwide'])} {raw_text}".strip()


def _detect_document_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if "pod" in normalized:
        return "pod"
    if any(keyword in normalized for keyword in ("ไม่ครบ", "ขาด")):
        return "missing_document"
    if any(keyword in normalized for keyword in ("จำเป็น", "บังคับ")):
        return "required_document"
    return "document_list"


def _build_document_knowledge_query(raw_text: str) -> str:
    subintent = _detect_document_subintent(raw_text)
    focus_map = {
        "document_list": "ต้องใช้เอกสารอะไรบ้าง document list",
        "required_document": "เอกสารไหนจำเป็น required document",
        "pod": "ต้องใช้ POD หรือไม่ proof of delivery",
        "missing_document": "ถ้าเอกสารไม่ครบต้องทำอย่างไร missing document",
    }
    return f"{focus_map.get(subintent, focus_map['document_list'])} {raw_text}".strip()


def _detect_timeline_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("ตัดรอบ", "cutoff")):
        return "cutoff"
    if any(keyword in normalized for keyword in ("เข้ารับ", "pickup")):
        return "pickup_window"
    if any(keyword in normalized for keyword in ("ช้า", "delay", "ปกติ")):
        return "delay_factor"
    return "transit_time"


def _build_timeline_knowledge_query(raw_text: str) -> str:
    subintent = _detect_timeline_subintent(raw_text)
    focus_map = {
        "transit_time": "ปกติใช้เวลากี่วัน timeline transit time SLA",
        "pickup_window": "มีรอบเข้ารับสินค้าไหม pickup window",
        "cutoff": "ตัดรอบกี่โมง cutoff time",
        "delay_factor": "อะไรทำให้ส่งช้ากว่าปกติ delay factor",
    }
    return f"{focus_map.get(subintent, focus_map['transit_time'])} {raw_text}".strip()


def _detect_general_subintent(text: str) -> str:
    normalized = normalize_intent_message(text)
    if any(keyword in normalized for keyword in ("เจ้าหน้าที่", "คุยกับคน", "human", "agent")):
        return "handoff"
    if any(keyword in normalized for keyword in ("ควรถามก่อน", "กรณีไหน", "แบบไหนควร")):
        return "consult_case"
    return "service_overview"


def _build_general_knowledge_query(raw_text: str) -> str:
    subintent = _detect_general_subintent(raw_text)
    focus_map = {
        "service_overview": "SiS Freight มีบริการอะไรบ้าง service overview",
        "handoff": "ถ้าต้องการเจ้าหน้าที่ต้องทำอย่างไร handoff human support",
        "consult_case": "งานแบบไหนควรทักมาสอบถามก่อน consult case",
    }
    return f"{focus_map.get(subintent, focus_map['service_overview'])} {raw_text}".strip()


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
    lowered = normalize_intent_message(raw_text)
    token_count = len(raw_text.split())
    is_long_form = len(raw_text) >= 120 or token_count >= 24

    if _contains_phrase(lowered, STRONG_SOLAR_KEYWORDS):
        solar_subintent = _detect_solar_subintent(raw_text)
        return ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query=_build_solar_knowledge_query(raw_text),
            top_k=4,
            threshold=0.52,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain what the Solar Hub service is, who it suits, the constraints, and the next step."
            ),
            preferred_answer_intent=solar_subintent,
        )

    if _contains_phrase(lowered, STRONG_BOOKING_KEYWORDS):
        booking_subintent = _detect_booking_subintent(raw_text)
        return ChatIntent(
            name="booking",
            lane="hybrid",
            knowledge_query=_build_booking_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on booking steps, what information is needed, service scope, and recommended next steps."
            ),
            preferred_answer_intent=booking_subintent,
        )

    if _contains_phrase(lowered, STRONG_PRICING_KEYWORDS):
        pricing_subintent = _detect_pricing_subintent(raw_text)
        return ChatIntent(
            name="pricing",
            lane="hybrid",
            knowledge_query=_build_pricing_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain price factors clearly and say what input data is still needed for an exact quote."
            ),
            preferred_answer_intent=pricing_subintent,
        )

    if _contains_phrase(lowered, STRONG_CLAIM_KEYWORDS):
        claim_subintent = _detect_claim_subintent(raw_text)
        return ChatIntent(
            name="claim",
            lane="hybrid",
            knowledge_query=_build_claim_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Guide the user step by step through claims or issue reporting and list the needed evidence."
            ),
            preferred_answer_intent=claim_subintent,
        )

    if _contains_phrase(lowered, STRONG_COVERAGE_KEYWORDS):
        coverage_subintent = _detect_coverage_subintent(raw_text)
        return ChatIntent(
            name="coverage",
            lane="hybrid",
            knowledge_query=_build_coverage_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on service coverage, destination eligibility, and next best steps when uncertain."
            ),
            preferred_answer_intent=coverage_subintent,
        )

    if _contains_phrase(lowered, STRONG_DOCUMENT_KEYWORDS):
        document_subintent = _detect_document_subintent(raw_text)
        return ChatIntent(
            name="document",
            lane="hybrid",
            knowledge_query=_build_document_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain required documents clearly and distinguish required vs optional paperwork."
            ),
            preferred_answer_intent=document_subintent,
        )

    if _contains_phrase(lowered, STRONG_TIMELINE_KEYWORDS):
        timeline_subintent = _detect_timeline_subintent(raw_text)
        return ChatIntent(
            name="timeline",
            lane="hybrid",
            knowledge_query=_build_timeline_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Clarify timing expectations and highlight what can affect the timeline."
            ),
            preferred_answer_intent=timeline_subintent,
        )

    if raw_text and len(raw_text) <= 20 and _contains_any(lowered, GREETING_KEYWORDS):
        return ChatIntent(
            name="greeting",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply briefly and warmly as Nong Godang.",
            canned_response="สวัสดีค้าบ น้องโกดังพร้อมช่วยเรื่องขนส่งและบริการน้า",
        )

    if raw_text and len(raw_text) <= 30 and _contains_any(lowered, THANKS_KEYWORDS):
        return ChatIntent(
            name="thanks",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply briefly and warmly as Nong Godang.",
            canned_response="ยินดีค้าบ ถ้ามีอะไรให้น้องโกดังช่วยต่อ ถามมาได้เลยน้า",
        )

    if _contains_any(lowered, HUMAN_KEYWORDS):
        return ChatIntent(
            name="human_handoff",
            lane="rule",
            knowledge_query="",
            top_k=0,
            threshold=0.0,
            system_hint="Reply clearly and politely.",
            canned_response="ได้เลยค้าบ ถ้าต้องการคุยกับเจ้าหน้าที่ แจ้งรายละเอียดที่ต้องการไว้ได้เลย เดี๋ยวน้องโกดังช่วยพาไปต่อให้ค้าบ",
        )

    if _contains_any(lowered, SOLAR_KEYWORDS):
        solar_subintent = _detect_solar_subintent(raw_text)
        return ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query=_build_solar_knowledge_query(raw_text),
            top_k=4,
            threshold=0.52,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain what the Solar Hub service is, who it suits, the constraints, and the next step."
            ),
            preferred_answer_intent=solar_subintent,
        )

    if _contains_any(lowered, BOOKING_KEYWORDS):
        booking_subintent = _detect_booking_subintent(raw_text)
        return ChatIntent(
            name="booking",
            lane="hybrid",
            knowledge_query=_build_booking_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on booking steps, what information is needed, service scope, and recommended next steps."
            ),
            preferred_answer_intent=booking_subintent,
        )

    if _contains_any(lowered, PRICING_KEYWORDS):
        pricing_subintent = _detect_pricing_subintent(raw_text)
        return ChatIntent(
            name="pricing",
            lane="hybrid",
            knowledge_query=_build_pricing_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain price factors clearly and say what input data is still needed for an exact quote."
            ),
            preferred_answer_intent=pricing_subintent,
        )

    if _contains_any(lowered, CLAIM_KEYWORDS):
        claim_subintent = _detect_claim_subintent(raw_text)
        return ChatIntent(
            name="claim",
            lane="hybrid",
            knowledge_query=_build_claim_knowledge_query(raw_text),
            top_k=5,
            threshold=0.55,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Guide the user step by step through claims or issue reporting and list the needed evidence."
            ),
            preferred_answer_intent=claim_subintent,
        )

    if _contains_any(lowered, COVERAGE_KEYWORDS):
        coverage_subintent = _detect_coverage_subintent(raw_text)
        return ChatIntent(
            name="coverage",
            lane="hybrid",
            knowledge_query=_build_coverage_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Focus on service coverage, destination eligibility, and next best steps when uncertain."
            ),
            preferred_answer_intent=coverage_subintent,
        )

    if _contains_any(lowered, DOCUMENT_KEYWORDS):
        document_subintent = _detect_document_subintent(raw_text)
        return ChatIntent(
            name="document",
            lane="hybrid",
            knowledge_query=_build_document_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Explain required documents clearly and distinguish required vs optional paperwork."
            ),
            preferred_answer_intent=document_subintent,
        )

    if _contains_any(lowered, TIME_KEYWORDS):
        timeline_subintent = _detect_timeline_subintent(raw_text)
        return ChatIntent(
            name="timeline",
            lane="hybrid",
            knowledge_query=_build_timeline_knowledge_query(raw_text),
            top_k=4,
            threshold=0.58,
            system_hint=(
                "Respond naturally in Thai as Nong Godang. "
                "Clarify timing expectations and highlight what can affect the timeline."
            ),
            preferred_answer_intent=timeline_subintent,
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
        knowledge_query=_build_general_knowledge_query(raw_text),
        top_k=3,
        threshold=0.60,
        system_hint=(
            "Respond naturally in Thai as Nong Godang. "
            "Be warm, concise, and helpful. If unsure, be honest and suggest the next best step."
        ),
        preferred_answer_intent=_detect_general_subintent(raw_text),
    )





