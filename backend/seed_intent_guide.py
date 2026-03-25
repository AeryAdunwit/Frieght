from __future__ import annotations

import os
from pathlib import Path
import json

from dotenv import load_dotenv

from backend.app.services.sheets_core import get_sheet_tab_link, get_write_sheets_service


load_dotenv()


GUIDE_TAB = "intent_guide"
GUIDE_HEADERS = [
    "topic",
    "base_intent",
    "family_alias_examples",
    "when_to_use",
    "sheet_example",
]

GUIDE_ROWS: list[list[str]] = [
    [
        "all",
        "blank",
        "",
        "ถ้าไม่แน่ใจ intent ปล่อยว่างได้ ระบบยังใช้ question + keywords + answer ได้ตามปกติ",
        "Solar หนักเท่าไหร่ | โดยทั่วไป Solar หนักประมาณเลทละ 1.2 ตัน | น้ำหนัก solar, กี่กิโล, กี่ตัน |  | yes",
    ],
    [
        "solar",
        "definition",
        "overview, intro, intro_definition",
        "ใช้กับคำถามภาพรวม เช่น Solar Hub คืออะไร หรือธุรกิจ EM คืออะไร",
        "บริการส่ง Solar ผ่าน Hub คืออะไร | เป็นบริการสำหรับงานขนส่งแผงโซลาร์ที่ต้องวางแผนเฉพาะทาง | solar hub, ธุรกิจ em | definition | yes",
    ],
    [
        "solar",
        "fit_use_case",
        "use_case, consult_case, fit_case",
        "ใช้กับคำถามว่าเหมาะกับงานแบบไหน หรือกรณีไหนควรใช้",
        "งานแบบไหนเหมาะกับบริการ Solar Hub | เหมาะกับงานที่มีหลายจุดส่งหรือมีข้อจำกัดหน้างาน | เหมาะกับงานแบบไหน, use case | fit_use_case | yes",
    ],
    [
        "solar",
        "required_info",
        "required_info_extra, prepare_info, info_required",
        "ใช้กับคำถามว่าต้องเตรียมข้อมูลหรือแจ้งอะไรบ้างก่อนประเมินงาน",
        "ถ้าจะใช้ Solar Hub ต้องเตรียมอะไรบ้าง | ควรแจ้งต้นทาง ปลายทาง จำนวนแผง รุ่นสินค้า และวันส่ง | เตรียมอะไร, ข้อมูลที่ต้องใช้ | required_info | yes",
    ],
    [
        "solar",
        "pricing",
        "pricing_policy, pricing_factor, price_quote, quotation",
        "ใช้กับคำถามเรื่องราคาของ Solar โดยตรง",
        "Solar แผ่นละเท่าไหร่ | ราคาไม่ตายตัว ขึ้นอยู่กับรุ่นและจำนวน | solar แผ่นละเท่าไหร่, ราคา solar ต่อแผ่น | pricing | yes",
    ],
    [
        "solar",
        "limitations",
        "restriction, condition, constraint",
        "ใช้กับคำถามเรื่องข้อจำกัดหรือเงื่อนไขของบริการ Solar",
        "Solar Hub มีข้อจำกัดอะไรบ้าง | ข้อจำกัดขึ้นอยู่กับหน้างานและรูปแบบการจัดวางสินค้า | ข้อจำกัด, เงื่อนไข | limitations | yes",
    ],
    [
        "solar",
        "weight",
        "weigh, น้ำหนัก, weight_check, solar_weight_detail",
        "ใช้กับคำถามเรื่องน้ำหนัก กี่กิโล กี่ตัน",
        "Solar หนักเท่าไหร่ | โดยทั่วไป Solar หนักประมาณเลทละ 1.2 ตัน | น้ำหนัก solar, กี่กิโล, กี่ตัน | weight | yes",
    ],
    [
        "booking",
        "booking_step",
        "booking_flow, booking_process, book_step",
        "ใช้กับคำถามเรื่องขั้นตอนการจองงาน",
        "ขั้นตอนการจองขนส่งมีอะไรบ้าง | เริ่มจากแจ้งรายละเอียดงานก่อน แล้วทีมจะช่วยจัดรอบรถ | ขั้นตอนจอง, booking step | booking_step | yes",
    ],
    [
        "booking",
        "booking_input",
        "booking_info, booking_detail, book_input, prepare_booking_info",
        "ใช้กับคำถามว่าต้องใช้ข้อมูลอะไรในการจอง",
        "ถ้าจะจองรถต้องเตรียมข้อมูลอะไร | ควรแจ้งต้นทาง ปลายทาง ประเภทสินค้า น้ำหนัก และวันรับงาน | จองรถใช้ข้อมูลอะไร | booking_input | yes",
    ],
    [
        "booking",
        "booking_timing",
        "booking_time, advance_booking, lead_time, booking_schedule",
        "ใช้กับคำถามเรื่องจองล่วงหน้าและเวลาที่ควรจอง",
        "ควรจองล่วงหน้าไหม | ควรจองล่วงหน้าหากเป็นงานใช้รถใหญ่หรือมีหลายจุดส่ง | จองล่วงหน้า, advance booking | booking_timing | yes",
    ],
    [
        "booking",
        "special_case",
        "custom_case, edge_case, booking_special_case",
        "ใช้กับเคสพิเศษ เช่น หลายจุดส่ง งานใช้รถเฉพาะทาง",
        "ถ้ามีหลายจุดส่งต้องแจ้งอะไรเพิ่ม | ควรแจ้งลำดับจุดส่งและข้อจำกัดของแต่ละจุด | หลายจุดส่ง, เคสพิเศษ | special_case | yes",
    ],
    [
        "pricing",
        "pricing_factor",
        "price_factor, rate_factor, pricing_detail",
        "ใช้กับคำถามว่าราคาคิดจากอะไรบ้าง",
        "ค่าขนส่งคิดจากอะไร | ราคาขึ้นอยู่กับระยะทาง น้ำหนัก และเงื่อนไขหน้างาน | คิดราคา, pricing factor | pricing_factor | yes",
    ],
    [
        "pricing",
        "quote_input",
        "quotation_input, quote_detail, pricing_input, price_input",
        "ใช้กับคำถามว่าขอราคาแล้วต้องส่งข้อมูลอะไรบ้าง",
        "ถ้าจะขอใบเสนอราคาต้องแจ้งอะไร | ควรแจ้งต้นทาง ปลายทาง ประเภทสินค้า และจำนวน | ขอราคา, quotation | quote_input | yes",
    ],
    [
        "pricing",
        "pricing_policy",
        "price_policy, rate_policy, pricing_rule, minimum_charge_policy",
        "ใช้กับคำถามเรื่องราคากลาง ขั้นต่ำ หรือกติกาการคิดราคา",
        "มีขั้นต่ำไหม | ราคาขั้นต่ำขึ้นอยู่กับประเภทงานและพื้นที่บริการ | ราคาขั้นต่ำ, pricing policy | pricing_policy | yes",
    ],
    [
        "pricing",
        "site_check",
        "site_survey, onsite_check, site_assessment",
        "ใช้กับคำถามว่างานแบบไหนต้องประเมินหน้างานก่อน",
        "งานแบบไหนต้องเช็กหน้างานก่อน | งานที่มีข้อจำกัดพื้นที่หรือเข้าถึงยากควรประเมินหน้างานก่อน | เช็กไซต์, site check | site_check | yes",
    ],
    [
        "claim",
        "claim_step",
        "claim_flow, claim_process, claim_howto",
        "ใช้กับคำถามเรื่องขั้นตอนการเคลม",
        "ถ้าสินค้าเสียหายต้องทำยังไง | ควรแจ้งเหตุและส่งรายละเอียดเคสให้ทีมตรวจสอบก่อน | เคลมยังไง, claim step | claim_step | yes",
    ],
    [
        "claim",
        "claim_input",
        "claim_detail, claim_info, incident_input",
        "ใช้กับคำถามว่าต้องแจ้งข้อมูลอะไรเมื่อเคลม",
        "ถ้าจะเคลมต้องแจ้งอะไรบ้าง | ควรแจ้งเลขงาน รายละเอียดความเสียหาย และเวลาที่พบเหตุ | แจ้งอะไรบ้าง, claim input | claim_input | yes",
    ],
    [
        "claim",
        "claim_evidence",
        "evidence_requirement, evidence_list, claim_proof, proof_required",
        "ใช้กับคำถามว่าต้องมีรูปหรือหลักฐานอะไรบ้าง",
        "เคลมต้องใช้หลักฐานอะไร | ควรมีรูปสินค้า จุดเสียหาย และหลักฐานประกอบการส่งมอบ | หลักฐานเคลม, claim evidence | claim_evidence | yes",
    ],
    [
        "claim",
        "claim_timeline",
        "claim_eta, claim_duration, claim_time",
        "ใช้กับคำถามว่าเคลมใช้เวลากี่วัน",
        "เคลมใช้เวลากี่วัน | ระยะเวลาขึ้นอยู่กับรายละเอียดเคสและหลักฐานครบถ้วนหรือไม่ | timeline claim, ใช้เวลากี่วัน | claim_timeline | yes",
    ],
    [
        "coverage",
        "nationwide",
        "all_area, all_regions, service_area",
        "ใช้กับคำถามว่าบริการครอบคลุมทั่วประเทศไหม",
        "ส่งได้ทั่วประเทศไหม | มีบริการครอบคลุมหลายพื้นที่ทั่วประเทศ ขึ้นอยู่กับเงื่อนไขงาน | ทั่วประเทศ, nationwide | nationwide | yes",
    ],
    [
        "coverage",
        "upcountry",
        "provincial_area, interprovince, ต่างจังหวัด",
        "ใช้กับคำถามเรื่องต่างจังหวัดหรือพื้นที่ต่างจังหวัด",
        "มีส่งต่างจังหวัดไหม | มีบริการต่างจังหวัดในหลายพื้นที่ | ต่างจังหวัด, upcountry | upcountry | yes",
    ],
    [
        "coverage",
        "restricted_area",
        "restricted_zone, hard_to_reach_area, remote_area",
        "ใช้กับคำถามเรื่องพื้นที่พิเศษหรือพื้นที่ที่ควรเช็กก่อน",
        "มีพื้นที่ไหนต้องเช็กก่อนบ้าง | บางพื้นที่ห่างไกลหรือมีข้อจำกัดการเข้าถึงควรเช็กก่อน | พื้นที่พิเศษ, restricted area | restricted_area | yes",
    ],
    [
        "coverage",
        "check_area",
        "area_check, coverage_check, destination_check",
        "ใช้กับคำถามว่าถ้ายังไม่แน่ใจปลายทางควรทำอย่างไร",
        "ถ้ายังไม่แน่ใจปลายทางต้องทำยังไง | แจ้งจังหวัดหรือจุดส่งมาเพื่อให้ช่วยเช็กพื้นที่บริการ | เช็กปลายทาง, check area | check_area | yes",
    ],
    [
        "documents",
        "document_list",
        "documents_list, doc_list, paper_list",
        "ใช้กับคำถามเรื่องรายการเอกสารที่ต้องใช้",
        "ต้องใช้เอกสารอะไรบ้าง | เอกสารขึ้นอยู่กับประเภทงานและข้อกำหนดของลูกค้า | เอกสารอะไรบ้าง, document list | document_list | yes",
    ],
    [
        "documents",
        "required_document",
        "document_required, mandatory_document, document_requirement",
        "ใช้กับคำถามว่าเอกสารไหนจำเป็นจริง",
        "เอกสารไหนจำเป็น | เอกสารที่จำเป็นขึ้นอยู่กับประเภทงานและรูปแบบการส่งมอบ | เอกสารจำเป็น, required document | required_document | yes",
    ],
    [
        "documents",
        "pod",
        "proof_of_delivery, delivery_proof, signed_pod",
        "ใช้กับคำถามเรื่อง POD หรือ proof of delivery",
        "ต้องใช้ POD ไหม | บางงานต้องใช้ POD เพื่อยืนยันการส่งมอบ | pod, proof of delivery | pod | yes",
    ],
    [
        "documents",
        "missing_document",
        "document_missing, missing_paper, incomplete_document",
        "ใช้กับคำถามว่าเอกสารไม่ครบต้องทำอย่างไร",
        "ถ้าเอกสารไม่ครบต้องทำยังไง | แจ้งรายการที่ขาดให้ชัดเพื่อให้ทีมช่วยประเมินทางเลือกต่อ | เอกสารไม่ครบ, missing document | missing_document | yes",
    ],
    [
        "timeline",
        "transit_time",
        "delivery_time, eta, sla_time",
        "ใช้กับคำถามเรื่องระยะเวลาขนส่งปกติ",
        "ปกติใช้เวลากี่วัน | ระยะเวลาขึ้นอยู่กับต้นทาง ปลายทาง และรอบรถ | ใช้เวลากี่วัน, transit time | transit_time | yes",
    ],
    [
        "timeline",
        "pickup_window",
        "pickup_time, pickup_slot, pickup_schedule",
        "ใช้กับคำถามเรื่องรอบรับของหรือเวลารับงาน",
        "มีรอบเข้ารับไหม | รอบรับขึ้นอยู่กับพื้นที่และตารางงานของรถ | pickup window, เข้ารับกี่โมง | pickup_window | yes",
    ],
    [
        "timeline",
        "cutoff",
        "cutoff_time, last_cutoff, round_cutoff",
        "ใช้กับคำถามเรื่องเวลาตัดรอบ",
        "ตัดรอบกี่โมง | เวลาตัดรอบขึ้นอยู่กับรอบรถและพื้นที่ให้บริการ | cutoff, ตัดรอบ | cutoff | yes",
    ],
    [
        "timeline",
        "delay_factor",
        "delay_reason, late_factor, timeline_delay",
        "ใช้กับคำถามว่ามีปัจจัยอะไรทำให้ช้าลง",
        "อะไรทำให้ส่งช้าได้บ้าง | ปัจจัยเช่นสภาพจราจร ระยะทาง และข้อจำกัดหน้างานมีผลต่อเวลา | delay factor, ส่งช้า | delay_factor | yes",
    ],
    [
        "general",
        "service_overview",
        "overview, service_intro, general_overview",
        "ใช้กับคำถามภาพรวมของบริการทั้งหมด",
        "SiS Freight มีบริการอะไรบ้าง | มีบริการขนส่งและงานเฉพาะทางหลายรูปแบบ | ภาพรวมบริการ, service overview | service_overview | yes",
    ],
    [
        "general",
        "handoff",
        "human_handoff, agent_handoff, contact_staff",
        "ใช้กับคำถามว่าต้องการคุยกับเจ้าหน้าที่หรือส่งต่อทีมงาน",
        "อยากคุยกับเจ้าหน้าที่ต้องทำยังไง | แจ้งข้อมูลเบื้องต้นมาได้ แล้วทีมจะช่วยประสานต่อ | handoff, ติดต่อเจ้าหน้าที่ | handoff | yes",
    ],
    [
        "general",
        "consult_case",
        "case_consult, advice_case, fit_case",
        "ใช้กับคำถามว่างานแบบไหนควรมาปรึกษาก่อน",
        "งานแบบไหนควรถามก่อน | ถ้างานมีข้อจำกัดหรือรายละเอียดหลายส่วนควรส่งข้อมูลมาปรึกษาก่อน | consult case, ปรึกษาเคส | consult_case | yes",
    ],
]


def _ensure_google_credentials_env() -> None:
    current = (os.environ.get("GOOGLE_CREDENTIALS") or "").strip()
    if current:
        try:
            json.loads(current)
            return
        except json.JSONDecodeError:
            pass

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    collecting = False
    buffer: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip()
        if not collecting and line.startswith("GOOGLE_CREDENTIALS="):
            _, value = line.split("=", 1)
            value = value.strip()
            if value:
                try:
                    json.loads(value)
                    os.environ["GOOGLE_CREDENTIALS"] = value
                    return
                except json.JSONDecodeError:
                    if value == "{":
                        collecting = True
                        buffer = ["{"]
                        continue
            collecting = True
            buffer = []
            continue

        if collecting:
            buffer.append(raw_line)
            if line.strip() == "}":
                os.environ["GOOGLE_CREDENTIALS"] = "\n".join(buffer).strip()
                return


def _ensure_tab(service, sheet_id: str, title: str) -> None:
    spreadsheet = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
    existing_titles = {sheet["properties"]["title"] for sheet in spreadsheet.get("sheets", [])}
    if title in existing_titles:
        return
    service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": title}}}]},
    ).execute()


def seed_intent_guide(sheet_id: str) -> str:
    if not sheet_id:
        raise ValueError("Missing SHEET_ID environment variable")

    _ensure_google_credentials_env()
    service = get_write_sheets_service()
    _ensure_tab(service, sheet_id, GUIDE_TAB)
    values = [GUIDE_HEADERS, *GUIDE_ROWS]
    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=f"'{GUIDE_TAB}'!A:Z",
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=f"'{GUIDE_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": values},
    ).execute()
    return get_sheet_tab_link(sheet_id, GUIDE_TAB)


if __name__ == "__main__":
    url = seed_intent_guide(os.environ.get("SHEET_ID", "").strip())
    print(url)
