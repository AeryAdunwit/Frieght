# Google Sheets Intent Guide

คู่มือนี้ใช้สำหรับกรอกคอลัมน์ `intent` ใน Google Sheet ให้ตรงกับ logic ที่ระบบรองรับจริงตอนนี้

## หลักสั้น ๆ

- ถ้าไม่แน่ใจ `intent` ให้ปล่อยว่างได้
- ระบบยัง sync และค้นจาก `question / keywords / answer` ได้ตามปกติ
- ควรใส่ `intent` เฉพาะตอนที่ต้องการบังคับคำตอบให้ตรง subtopic มากขึ้น
- ถ้าจะสร้าง intent ย่อยใหม่ ให้ตั้งชื่อให้เกาะกับ family หลักที่ระบบรู้จัก

## Intent ใหม่ที่ระบบรองรับได้แบบยืดหยุ่น

ตอนนี้ระบบรองรับ `intent` ย่อยใหม่ได้มากขึ้น ถ้าตั้งชื่อให้อยู่ใน family ที่ถูกต้อง เช่น:

- `pricing_policy`
- `pricing_factor`
- `price_quote`
- `required_info_extra`
- `booking_input_detail`
- `weight_check`
- `solar_weight_detail`

หลักคือให้ชื่อ `intent` มีคำหลักของ family อยู่ในชื่อ เช่น:

- กลุ่มราคา: มีคำว่า `pricing`, `price`, `quote`
- กลุ่มข้อมูลที่ต้องใช้: มีคำว่า `required_info`, `booking_input`, `claim_input`, `quote_input`, `prepare`
- กลุ่มน้ำหนัก: มีคำว่า `weight`, `weigh`, `น้ำหนัก`
- กลุ่มข้อจำกัด: มีคำว่า `limitations`, `condition`, `constraint`
- กลุ่มภาพรวม/นิยาม: มีคำว่า `definition`, `overview`
- กลุ่มการจอง: มีคำว่า `booking_step`, `booking_input`, `booking_timing`, `special_case`
- กลุ่มเคลม: มีคำว่า `claim_step`, `claim_input`, `claim_evidence`, `claim_timeline`
- กลุ่มพื้นที่บริการ: มีคำว่า `nationwide`, `upcountry`, `restricted_area`, `check_area`
- กลุ่มเอกสาร: มีคำว่า `document_list`, `required_document`, `pod`, `missing_document`
- กลุ่มเวลา: มีคำว่า `transit_time`, `pickup_window`, `cutoff`, `delay_factor`
- กลุ่มทั่วไป: มีคำว่า `service_overview`, `handoff`, `consult_case`

ถ้าตั้งชื่อหลุดจาก family มากเกินไป ระบบอาจ sync ได้ แต่ไม่ช่วยเรื่องการบังคับคำตอบ

ตัวอย่างชื่อที่ระบบจับ family ได้ทันที:

- `booking_process_detail`
- `prepare_booking_info`
- `claim_proof_detail`
- `coverage_check_detail`
- `timeline_cutoff_policy`
- `service_intro_detail`

## Header ที่ต้องใช้

```text
question | answer | keywords | intent | active
```

## กติกาการใช้ `intent`

- `intent` ว่าง: ใช้ได้
- `active = yes`: ใช้งาน
- `active = no`: ไม่ถูก sync เข้า knowledge ที่ใช้งานจริง
- ถ้าคำถามเดียวกันมีหลายมุม ให้แยกหลายแถว ไม่ควรรวมหลาย intent ในแถวเดียว

## Intent ที่รองรับจริงตามแต่ละ tab

### `solar`

ใช้ได้:
- `definition`
- `fit_use_case`
- `required_info`
- `pricing`
- `limitations`
- `weight`

ใช้ได้แบบ alias:
- `weigh`
- `น้ำหนัก`

แนะนำใช้เมื่อ:
- `definition`: ถามว่า Solar Hub คืออะไร, ธุรกิจ EM คืออะไร
- `fit_use_case`: เหมาะกับงานแบบไหน, ใช้กรณีไหน
- `required_info`: ต้องเตรียมอะไร, ต้องแจ้งอะไร
- `pricing`: คิดราคาอย่างไร, ประเมินราคา
- `limitations`: ข้อจำกัด, เงื่อนไข, ต้องระวังอะไร
- `weight`: หนักเท่าไหร่, กี่กิโล, กี่ตัน

ตัวอย่าง:

```text
Solar หนักเท่าไหร่ | โดยทั่วไป Solar หนักประมาณเลทละ 1.2 ตันค้าบ | น้ำหนัก solar, solar หนักเท่าไหร่, กี่กิโล, กี่ตัน | weight | yes
```

### `booking`

ใช้ได้:
- `booking_step`
- `booking_input`
- `booking_timing`
- `special_case`

แนะนำใช้เมื่อ:
- `booking_step`: จองยังไง, ขั้นตอนจอง
- `booking_input`: ต้องใช้ข้อมูลอะไร
- `booking_timing`: ต้องจองล่วงหน้าไหม
- `special_case`: งานพิเศษ, หลายจุดส่ง, รถใหญ่

### `pricing`

ใช้ได้:
- `pricing_factor`
- `quote_input`
- `pricing_policy`
- `site_check`

แนะนำใช้เมื่อ:
- `pricing_factor`: ราคาคิดจากอะไร
- `quote_input`: ขอราคา ต้องส่งข้อมูลอะไร
- `pricing_policy`: มีราคากลางไหม, ขั้นต่ำเท่าไหร่
- `site_check`: งานแบบไหนต้องประเมินหน้างาน

### `claim`

ใช้ได้:
- `claim_step`
- `claim_input`
- `claim_evidence`
- `claim_timeline`

แนะนำใช้เมื่อ:
- `claim_step`: ต้องทำอย่างไรเมื่อเคลม
- `claim_input`: ต้องแจ้งอะไรบ้าง
- `claim_evidence`: ต้องใช้รูปหรือหลักฐานอะไร
- `claim_timeline`: ใช้เวลากี่วัน

### `coverage`

ใช้ได้:
- `nationwide`
- `upcountry`
- `restricted_area`
- `check_area`

แนะนำใช้เมื่อ:
- `nationwide`: ส่งได้ทั่วประเทศไหม
- `upcountry`: ส่งต่างจังหวัดไหม
- `restricted_area`: พื้นที่ไหนต้องเช็กก่อน
- `check_area`: ถ้ายังไม่แน่ใจปลายทางต้องทำอย่างไร

### `documents`

ใช้ได้:
- `document_list`
- `required_document`
- `pod`
- `missing_document`

แนะนำใช้เมื่อ:
- `document_list`: ต้องใช้เอกสารอะไรบ้าง
- `required_document`: เอกสารไหนจำเป็น
- `pod`: ต้องใช้ POD หรือไม่
- `missing_document`: ถ้าเอกสารไม่ครบต้องทำอย่างไร

### `timeline`

ใช้ได้:
- `transit_time`
- `pickup_window`
- `cutoff`
- `delay_factor`

แนะนำใช้เมื่อ:
- `transit_time`: ปกติใช้เวลากี่วัน
- `pickup_window`: มีรอบเข้ารับไหม
- `cutoff`: ตัดรอบกี่โมง
- `delay_factor`: อะไรทำให้ล่าช้า

### `general`

ใช้ได้:
- `service_overview`
- `handoff`
- `consult_case`

แนะนำใช้เมื่อ:
- `service_overview`: มีบริการอะไรบ้าง
- `handoff`: ถ้าต้องการคุยกับเจ้าหน้าที่
- `consult_case`: งานแบบไหนควรมาถามก่อน

## เมื่อไรควรปล่อย `intent` ว่าง

ควรปล่อยว่างเมื่อ:
- เป็นคำถามทั่วไปที่ไม่ต้องบังคับ subtopic
- ยังไม่แน่ใจว่าควรจัดเข้าหมวดย่อยไหน
- ต้องการให้ระบบใช้ `question + keywords` ช่วยจับเอง

ไม่ควรปล่อยว่างเมื่อ:
- มีหลายแถวใน tab เดียวกันที่ใกล้กันมาก
- อยากบังคับให้คำตอบดึงแถวเฉพาะจริง ๆ
- เป็นหมวดที่มีหลายมุมชัด เช่น `pricing`, `timeline`, `solar`

## วิธีใช้งานหลังแก้ชีต

1. แก้ Google Sheet
2. กด `sync knowledge ตอนนี้`
3. รอให้ sync สำเร็จ
4. ทดสอบด้วยคำถามจริงที่ใกล้กับ `question` หรือ `keywords`

## ถ้ายังไม่ตอบตามที่กรอก

เช็กตามนี้:

1. ข้อมูลถูกใส่ใน tab ถูกหมวดหรือยัง
2. `active` เป็น `yes` หรือยัง
3. กด `sync knowledge ตอนนี้` แล้วหรือยัง
4. แถวใหม่เข้า `knowledge_base` แล้วหรือยัง
5. คำถามจริงของ user อยู่ใกล้กับ `question / keywords` มากพอหรือยัง
6. ใส่ `intent` ใหม่ที่โค้ดยังไม่รองรับอยู่หรือไม่

## ข้อแนะนำสำหรับทีม

- ถ้าไม่แน่ใจ ให้ปล่อย `intent` ว่างก่อน
- ถ้าจะใส่ `intent` ให้เลือกจากคู่มือนี้เท่านั้น
- ถ้าอยากได้ intent ใหม่มาก ๆ ให้พยายามตั้งชื่อให้เกาะ family หลักก่อน
- ถ้าเป็น intent ใหม่ที่ไม่เข้ากลุ่มเดิมจริง ๆ ค่อยแจ้งทีม dev
