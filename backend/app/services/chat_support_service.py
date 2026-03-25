from __future__ import annotations

import ast
import re
from dataclasses import replace

from .intent_router_core import ChatIntent
from .runtime_support import INTENT_TOPIC_MAP
from .vector_search_core import load_topic_rows, search_knowledge


def build_history(history) -> list[dict]:
    trimmed_history = history[-10:]
    return [{"role": turn.role, "parts": [turn.content]} for turn in trimmed_history]


def build_intent_prompt(intent: ChatIntent) -> str:
    return (
        f"\n\n[INTENT]\n"
        f"name={intent.name}\n"
        f"lane={intent.lane}\n"
        f"instruction={intent.system_hint}"
    )


def normalize_response_mode(response_mode: str | None) -> str:
    mode = (response_mode or "quick").strip().lower()
    return "detail" if mode == "detail" else "quick"


def build_response_mode_prompt(response_mode: str | None) -> str:
    mode = normalize_response_mode(response_mode)
    if mode == "detail":
        return (
            "\n\n[RESPONSE MODE]\n"
            "mode=detail\n"
            "instruction=ตอบให้ครบขึ้นอีกนิดได้ แต่ยังต้องอ่านง่าย แยกเป็นบรรทัดสั้น ๆ "
            "และปิดท้ายด้วย next step ที่ชัดเจน"
        )
    return (
        "\n\n[RESPONSE MODE]\n"
        "mode=quick\n"
        "instruction=ตอบให้สั้น ตรง และไว เน้น 2-3 บรรทัดพอ ถ้าไม่จำเป็นอย่าขยายเยอะ"
    )


def enhance_intent(intent: ChatIntent) -> ChatIntent:
    if intent.name == "greeting":
        return replace(intent, canned_response="สวัสดีค้าบ ถามงานได้เลย หรือจะคุยเล่นนิดนึงก็ไหวค้าบ")
    if intent.name == "thanks":
        return replace(
            intent,
            canned_response="ยินดีค้าบ มีต่อก็โยนมาได้เลย น้องโกดังยังอยู่หน้าโกดังเหมือนเดิม",
        )
    if intent.name == "human_handoff":
        return replace(
            intent,
            canned_response="ได้ค้าบ ถ้าจะคุยกับทีมงาน กดติดต่อเจ้าหน้าที่หรือฝากข้อมูลให้ทีมติดต่อกลับได้เลย เดี๋ยวน้องพาไปต่อให้",
        )
    if intent.name in {"general_chat", "longform_consult", "solar"}:
        return replace(
            intent,
            system_hint=(
                intent.system_hint
                + " Keep the tone warm, human, and conversational. "
                + "If the user seems lonely or wants to chat, you may respond a bit longer with gentle companionship "
                + "before guiding them back to useful freight help when appropriate. "
                + "Still keep the answer punchy, easy to scan, and answer-first."
            ),
        )
    return intent


def enforce_nong_godang_voice(text: str) -> str:
    if not text:
        return text

    normalized = re.sub(r"```json\s*.*?```", "", text, flags=re.IGNORECASE | re.DOTALL)
    normalized = re.sub(r"\[SYSTEM DATA\].*?(?=\n{2,}|\Z)", "", normalized, flags=re.IGNORECASE | re.DOTALL)
    normalized = re.sub(r"\[SYSTEM DATA:[^\]]*\]", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^\s*json\s*\{.*$", "", normalized, flags=re.IGNORECASE | re.MULTILINE)
    normalized = re.sub(
        r"^\s*[\{\[].*(tracking_results|estimated_delivery|out for delivery|details).*$",
        "",
        normalized,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if not normalized:
        normalized = text

    replacements = [
        ("SiS Freight", ""),
        ("sis freight", ""),
        ("SIS Freight", ""),
        ("พี่โกดัง", "น้องโกดัง"),
        ("หนู", "น้องโกดัง"),
        ("ดิฉัน", "น้องโกดัง"),
        ("ฉัน", "น้องโกดัง"),
        ("นะคะ", "น้า"),
        ("นะค่ะ", "น้า"),
        ("นะครับ", "น้า"),
        ("ค่ะ", "ค้าบ"),
        ("คะ", "ค้าบ"),
        ("ครับ", "ค้าบ"),
        ("เลยค่ะ", "เลยค้าบ"),
        ("ได้ค่ะ", "ได้ค้าบ"),
        ("ได้คะ", "ได้ค้าบ"),
        ("ใช่ไหมคะ", "ใช่ไหมค้าบ"),
        ("ไหมคะ", "ไหมค้าบ"),
        ("ด้วยค่ะ", "ด้วยค้าบ"),
    ]
    for old, new in replacements:
        normalized = normalized.replace(old, new)

    for old, new in [
        ("ของ  ", " "),
        ("ของ น้า", "น้า"),
        ("  ", " "),
        (" ,", ","),
        (" .", "."),
        ("  ", " "),
    ]:
        normalized = normalized.replace(old, new)

    if "น้องโกดัง" not in normalized and ("สวัสดี" in normalized or "ยินดี" in normalized):
        normalized = normalized.replace("สวัสดี", "สวัสดีค้าบ จากน้องโกดัง")

    return normalized.strip()


def search_knowledge_rows(message: str, top_k: int = 3, threshold: float = 0.65) -> list[dict]:
    return search_knowledge(message, top_k=top_k, threshold=threshold)


def knowledge_rows_to_context(results: list[dict]) -> str:
    if not results:
        return "Knowledge Base:\nNo relevant information found in the knowledge base."

    lines = [f"[{row['topic']}] Q: {row['question']}\nA: {row['answer']}" for row in results]
    return "Knowledge Base:\n" + "\n\n".join(lines)


def tokenize_thaiish(text: str) -> list[str]:
    cleaned = (
        (text or "")
        .lower()
        .replace("?", " ")
        .replace(",", " ")
        .replace("/", " ")
        .replace("-", " ")
        .replace("_", " ")
        .replace("(", " ")
        .replace(")", " ")
    )
    return [token.strip() for token in cleaned.split() if token.strip()]


def topic_fallback_rows(intent: ChatIntent, user_message: str, max_items: int = 2) -> list[dict]:
    expected_topics = INTENT_TOPIC_MAP.get(intent.name)
    if not expected_topics:
        return []

    candidate_rows: list[dict] = []
    for topic in expected_topics:
        candidate_rows.extend(load_topic_rows(topic))

    if not candidate_rows:
        return []

    message = (user_message or "").strip().lower()
    message_tokens = set(tokenize_thaiish(message))
    scored_rows: list[tuple[int, dict]] = []
    for row in candidate_rows:
        question = (row.get("question") or "").strip().lower()
        keywords = (row.get("keywords") or "").strip().lower()
        content = (row.get("content") or "").strip().lower()
        answer = (row.get("answer") or "").strip()
        if not answer:
            continue

        score = 0
        if question == message:
            score += 100
        if message and message in question:
            score += 30

        row_tokens = set(tokenize_thaiish(question))
        keyword_tokens = {token.strip() for token in keywords.replace(",", " ").split() if token.strip()}
        content_tokens = set(tokenize_thaiish(content))
        score += len(message_tokens & row_tokens) * 6
        score += len(message_tokens & keyword_tokens) * 4
        score += len(message_tokens & content_tokens) * 2
        if score > 0:
            scored_rows.append((score, row))

    scored_rows.sort(key=lambda item: item[0], reverse=True)
    if scored_rows:
        return [row for _, row in scored_rows[:max_items]]
    return candidate_rows[:max_items]


def rows_for_intent(intent: ChatIntent, rows: list[dict]) -> list[dict]:
    expected_topics = INTENT_TOPIC_MAP.get(intent.name)
    if not expected_topics:
        return rows
    filtered = [row for row in rows if (row.get("topic") or "").strip().lower() in expected_topics]
    return filtered or rows


def rows_for_preferred_answer_intent(intent: ChatIntent, rows: list[dict]) -> list[dict]:
    preferred = (intent.preferred_answer_intent or "").strip().lower()
    if not preferred:
        return rows
    filtered = [row for row in rows if (row.get("intent") or "").strip().lower() == preferred]
    return filtered or rows


def direct_topic_intent_rows(intent: ChatIntent, user_message: str) -> list[dict]:
    expected_topics = INTENT_TOPIC_MAP.get(intent.name)
    preferred = (intent.preferred_answer_intent or "").strip().lower()
    if not expected_topics or not preferred:
        return []

    candidate_rows: list[dict] = []
    for topic in expected_topics:
        candidate_rows.extend(load_topic_rows(topic))

    candidate_rows = [
        row for row in candidate_rows if (row.get("intent") or "").strip().lower() == preferred
    ]
    if not candidate_rows:
        return []

    message = (user_message or "").strip().lower()
    message_tokens = set(tokenize_thaiish(message))
    scored_rows: list[tuple[int, dict]] = []
    for row in candidate_rows:
        question = (row.get("question") or "").strip().lower()
        keywords = (row.get("keywords") or "").strip().lower()
        content = (row.get("content") or "").strip().lower()
        answer = (row.get("answer") or "").strip()
        if not answer:
            continue

        score = 0
        if question == message:
            score += 100
        if message and message in question:
            score += 40

        row_tokens = set(tokenize_thaiish(question))
        keyword_tokens = {token.strip() for token in keywords.replace(",", " ").split() if token.strip()}
        content_tokens = set(tokenize_thaiish(content))
        score += len(message_tokens & row_tokens) * 6
        score += len(message_tokens & keyword_tokens) * 4
        score += len(message_tokens & content_tokens) * 2
        scored_rows.append((score, row))

    scored_rows.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored_rows[:2]]


def resolve_knowledge_rows(intent: ChatIntent, user_message: str) -> list[dict]:
    direct_rows = direct_topic_intent_rows(intent, user_message)
    if direct_rows:
        return direct_rows

    primary_rows = search_knowledge_rows(
        intent.knowledge_query or user_message,
        top_k=intent.top_k,
        threshold=intent.threshold,
    )
    primary_rows = rows_for_intent(intent, primary_rows)
    primary_rows = rows_for_preferred_answer_intent(intent, primary_rows)
    if primary_rows:
        return primary_rows

    if intent.name in INTENT_TOPIC_MAP:
        fallback_rows = search_knowledge_rows(
            user_message,
            top_k=max(intent.top_k, 5),
            threshold=max(0.42, intent.threshold - 0.16),
        )
        filtered_fallback_rows = rows_for_intent(intent, fallback_rows)
        filtered_fallback_rows = rows_for_preferred_answer_intent(intent, filtered_fallback_rows)
        if filtered_fallback_rows:
            return filtered_fallback_rows

        topic_rows = topic_fallback_rows(intent, user_message)
        topic_rows = rows_for_preferred_answer_intent(intent, topic_rows)
        if topic_rows:
            return topic_rows

    return primary_rows


def format_direct_kb_reply(intent: ChatIntent, rows: list[dict], response_mode: str = "quick") -> str:
    if not rows:
        return ""

    lead_map = {
        "coverage": "เช็กพื้นที่บริการให้ตรงคำถามแล้วค้าบ",
        "document": "เอกสารที่ต้องเช็กมีประมาณนี้ค้าบ",
        "timeline": "เรื่องเวลา น้องสรุปให้ไว ๆ ค้าบ",
    }
    closing_map = {
        "coverage": "ถ้ายังไม่ชัวร์เรื่องปลายทาง บอกจังหวัดหรือจุดส่งมาได้ เดี๋ยวน้องช่วยไล่ต่อ",
        "document": "ถ้าจะให้เช็กเอกสารตามงานจริง ส่งประเภทงานหรือรายการที่มีมาได้เลยค้าบ",
        "timeline": "ถ้าจะให้กะเวลาตามงานจริง ส่งต้นทาง ปลายทาง และวันรับงานมาได้เลยค้าบ",
    }

    mode = normalize_response_mode(response_mode)
    max_rows = 2 if mode == "detail" else 1
    lines = [lead_map.get(intent.name, "น้องโกดังสรุปให้สั้น ๆ ค้าบ")]
    seen_answers: set[str] = set()
    for row in rows[:max_rows]:
        answer = (row.get("answer") or "").strip()
        if not answer or answer in seen_answers:
            continue
        seen_answers.add(answer)
        lines.append(answer)

    closing = closing_map.get(intent.name)
    if closing:
        lines.append(closing)

    return enforce_nong_godang_voice("\n".join(lines))


def _select_distinct_answers(rows: list[dict], max_items: int = 3) -> list[str]:
    answers: list[str] = []
    seen: set[str] = set()
    for row in rows:
        answer = (row.get("answer") or "").strip()
        if not answer or answer in seen:
            continue
        seen.add(answer)
        answers.append(answer)
        if len(answers) >= max_items:
            break
    return answers


def _has_route_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("ต้นทาง", "ปลายทาง", "จาก", "ไป", "รับจาก", "ส่งไป", "ถึง"))


def _has_quantity_hint(text: str) -> bool:
    lowered = text.lower()
    return bool(re.search(r"\d", lowered)) and any(
        token in lowered for token in ("แผง", "ชิ้น", "พาเลท", "พาเลต", "ลัง", "กล่อง", "กก", "kg", "ตัน", "คัน")
    )


def _has_schedule_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("วันนี้", "พรุ่งนี้", "สัปดาห์", "อาทิตย์", "วันที่", "เช้า", "บ่าย", "เย็น", "ด่วน"))


def _has_product_hint(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("สินค้า", "solar", "โซลาร์", "แผง", "inverter", "อินเวอร์เตอร์", "พาเลท", "อะไหล่", "เครื่อง"))


def normalize_basic_math_expression(message: str) -> str:
    normalized = (message or "").strip().lower()
    if not normalized or len(normalized) > 48:
        return ""

    for phrase in (
        "เท่าไหร่",
        "เท่าไร",
        "ได้อะไร",
        "ได้เท่าไหร่",
        "ได้เท่าไร",
        "คืออะไร",
        "ได้ไหม",
        "ช่วยคิด",
        "คิดให้หน่อย",
        "คำนวณให้หน่อย",
        "?",
        "=",
    ):
        normalized = normalized.replace(phrase, "")

    normalized = normalized.replace("x", "*").replace("×", "*").replace("÷", "/")
    normalized = re.sub(r"\s+", "", normalized)

    if not re.fullmatch(r"[\d.+\-*/()]+", normalized):
        return ""
    if not re.search(r"[+\-*/]", normalized):
        return ""
    if len(re.findall(r"\d+", normalized)) < 2:
        return ""
    return normalized


def _safe_eval_basic_math(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval_basic_math(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Num):
        return float(node.n)  # type: ignore[arg-type]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _safe_eval_basic_math(node.operand)
        return operand if isinstance(node.op, ast.UAdd) else -operand
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        left = _safe_eval_basic_math(node.left)
        right = _safe_eval_basic_math(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if right == 0:
            raise ZeroDivisionError("division by zero")
        return left / right
    raise ValueError("unsupported math expression")


def _format_basic_math_result(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def build_basic_math_reply(message: str) -> str | None:
    expression = normalize_basic_math_expression(message)
    if not expression:
        return None

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _safe_eval_basic_math(parsed)
    except ZeroDivisionError:
        return "ข้อนี้หารด้วยศูนย์ไม่ได้นะค้าบ"
    except (SyntaxError, TypeError, ValueError):
        return None

    if abs(result) > 1_000_000_000_000:
        return None

    pretty_expression = expression.replace("*", " × ").replace("/", " ÷ ").replace("+", " + ").replace("-", " - ")
    pretty_expression = re.sub(r"\s+", " ", pretty_expression).strip()
    return f"{pretty_expression} = {_format_basic_math_result(result)} ค้าบ"


def build_missing_info_prompt(intent: ChatIntent, user_message: str, context_text: str = "") -> str:
    lowered = f"{context_text} {user_message}".lower().strip()

    if intent.name == "solar":
        missing: list[str] = []
        if not _has_route_hint(lowered):
            missing.append("ต้นทาง/ปลายทาง")
        if not _has_quantity_hint(lowered):
            missing.append("จำนวนแผงหรือจำนวนสินค้า")
        if not _has_product_hint(lowered):
            missing.append("รุ่นหรือประเภทสินค้า")
        if not _has_schedule_hint(lowered):
            missing.append("วันส่งหรือช่วงเวลาที่ต้องการ")
        if missing:
            return "ถ้าจะให้ช่วยต่อ ส่งเพิ่มอีกนิดค้าบ: " + ", ".join(missing[:4])
        return "ข้อมูลหลักมาครบประมาณหนึ่งแล้วค้าบ ถ้าพร้อม ส่งรายละเอียดเพิ่มได้เลย เดี๋ยวน้องไล่ต่อให้"

    if intent.name == "pricing":
        missing = []
        if not _has_route_hint(lowered):
            missing.append("ต้นทาง/ปลายทาง")
        if not _has_product_hint(lowered):
            missing.append("ประเภทสินค้า")
        if not _has_quantity_hint(lowered):
            missing.append("น้ำหนัก ขนาด หรือจำนวน")
        if missing:
            return "ถ้าจะประเมินต่อ ส่งเพิ่มอีกนิดค้าบ: " + ", ".join(missing[:4])
        return "ถ้ารายละเอียดครบแล้ว ส่งมาเพิ่มได้เลยค้าบ เดี๋ยวน้องช่วยประเมินต่อให้"

    if intent.name == "booking":
        missing = []
        if not _has_route_hint(lowered):
            missing.append("ต้นทาง/ปลายทาง")
        if not _has_product_hint(lowered):
            missing.append("ประเภทสินค้า")
        if not _has_quantity_hint(lowered):
            missing.append("จำนวนหรือขนาดงาน")
        if not _has_schedule_hint(lowered):
            missing.append("วันที่หรือช่วงเวลาที่อยากเข้ารับ")
        if missing:
            return "ถ้าจะจองต่อ ส่งเพิ่มอีกนิดค้าบ: " + ", ".join(missing[:4])
        return "ข้อมูลเริ่มครบแล้วค้าบ ถ้าพร้อม ส่งต่อมาได้เลย เดี๋ยวน้องช่วยแตกขั้นตอนให้"

    if intent.name == "claim":
        missing = []
        lowered_has_issue = any(token in lowered for token in ("เสียหาย", "ชำรุด", "หาย", "ส่งผิด", "แตก", "บุบ", "ปัญหา"))
        lowered_has_evidence = any(token in lowered for token in ("รูป", "ภาพ", "หลักฐาน", "วิดีโอ", "video"))
        if not re.search(r"\b\d{8,}\b", user_message or ""):
            missing.append("เลขงานหรือเลข DO")
        if not lowered_has_issue:
            missing.append("อาการปัญหา")
        if not lowered_has_evidence:
            missing.append("รูปหรือหลักฐานที่มี")
        if missing:
            return "ถ้าจะเดินเรื่องต่อ ส่งเพิ่มอีกนิดค้าบ: " + ", ".join(missing[:4])
        return "เคสนี้เริ่มเดินต่อได้แล้วค้าบ ถ้าสะดวก แนบรายละเอียดเพิ่มมาอีกนิด เดี๋ยวน้องช่วยต่อให้"

    return ""


def recent_text_from_history(history, user_message: str, max_turns: int = 10) -> str:
    recent_parts = [turn.content for turn in history[-max_turns:] if getattr(turn, "content", "").strip()]
    recent_parts.append(user_message)
    return "\n".join(part for part in recent_parts if part).strip()


def format_specialized_reply(
    intent: ChatIntent,
    user_message: str,
    rows: list[dict],
    response_mode: str = "quick",
    context_text: str = "",
) -> str:
    if not rows:
        return ""

    lowered = user_message.lower()
    mode = normalize_response_mode(response_mode)
    answers = _select_distinct_answers(rows, max_items=3)
    if not answers:
        return ""

    solar_lead_map = {
        "definition": "Solar ผ่าน Hub คือบริการประมาณนี้ค้าบ",
        "fit_use_case": "ถ้างานประมาณนี้ ใช้ Solar Hub ได้ค้าบ",
        "required_info": "ถ้าจะเริ่มงานนี้ ส่งข้อมูลประมาณนี้มาก่อนได้เลยค้าบ",
        "pricing": "เรื่องราคา Solar ดูจากรายละเอียดงานก่อนค้าบ",
        "limitations": "จุดที่ต้องระวังของ Solar มีประมาณนี้ค้าบ",
    }
    lead_map = {
        "solar": solar_lead_map.get((intent.preferred_answer_intent or "").strip().lower(), "Solar ผ่าน Hub คือบริการประมาณนี้ค้าบ"),
        "booking": "ถ้าจะจองงาน ทำตามนี้ได้เลยค้าบ",
        "pricing": "ถ้าถามเรื่องราคา น้องตอบตรงนี้ก่อนค้าบ",
        "claim": "ถ้ามีเคสเคลม ทำตามนี้ก่อนค้าบ",
    }
    closing_map = {
        "solar": "ถ้าจะให้ช่วยต่อ ส่งต้นทาง ปลายทาง จำนวนแผง รุ่นสินค้า และวันส่งมาได้เลยค้าบ",
        "booking": "ถ้าจะให้ช่วยจองต่อ ส่งต้นทาง ปลายทาง ประเภทสินค้า จำนวน และช่วงเวลาที่อยากเข้ารับมาได้เลยค้าบ",
        "pricing": "ถ้าจะให้ประเมินต่อ ส่งต้นทาง ปลายทาง ประเภทสินค้า น้ำหนักหรือขนาด และจำนวนมาได้เลยค้าบ",
        "claim": "ถ้าจะเดินเรื่องต่อ ส่งเลขงาน อาการปัญหา และรูปที่มีมาได้เลยค้าบ",
    }

    lines = [lead_map.get(intent.name, "น้องโกดังสรุปให้ก่อนค้าบ")]

    if intent.name == "solar":
        lines.append(answers[0])
        if any(keyword in lowered for keyword in ("ราคา", "ประเมิน", "quote", "quotation")):
            lines.append("งาน Solar ไม่มีราคากลางตายตัว ต้องดูรายละเอียดหน้างานก่อนค้าบ")
        elif (
            len(answers) > 1
            and mode == "detail"
            and any(
                keyword in lowered
                for keyword in ("เหมาะ", "งานแบบไหน", "ใช้กับ", "กรณีไหน", "เตรียม", "ข้อมูล", "ต้องใช้", "เอกสาร", "ข้อจำกัด", "เงื่อนไข", "ต้องระวัง", "จำกัด")
            )
        ):
            lines.append(answers[1])
    elif intent.name == "booking":
        lines.extend(answers[: (2 if mode == "detail" else 1)])
        if any(keyword in lowered for keyword in ("จองล่วงหน้า", "ล่วงหน้า", "advance")):
            lines.append("ถ้างานหลายจุดหรือรถใหญ่ จองล่วงหน้าไว้ก่อน จะลื่นกว่าค้าบ")
    elif intent.name == "pricing":
        lines.extend(answers[: (2 if mode == "detail" else 1)])
        if "ราคากลาง" in lowered or "ขั้นต่ำ" in lowered:
            lines.append("ราคาขึ้นกับงานจริงค้าบ ถ้าอยากชัด ส่งรายละเอียดมา เดี๋ยวน้องช่วยไล่ให้")
    elif intent.name == "claim":
        lines.extend(answers[: (2 if mode == "detail" else 1)])
        if any(keyword in lowered for keyword in ("ด่วน", "รีบ", "urgent")):
            lines.append("ถ้าเคสด่วน ส่งรายละเอียดกับหลักฐานมาให้ครบตั้งแต่รอบแรก จะเดินเรื่องไวขึ้นค้าบ")
    else:
        lines.extend(answers[: (2 if mode == "detail" else 1)])

    missing_prompt = build_missing_info_prompt(intent, user_message, context_text)
    lines.append(missing_prompt or closing_map.get(intent.name, "ถ้าจะให้ช่วยต่อ ส่งรายละเอียดเพิ่มมาได้เลยค้าบ"))
    return enforce_nong_godang_voice("\n".join(lines))
