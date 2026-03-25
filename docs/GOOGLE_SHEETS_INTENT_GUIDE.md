# Google Sheets Intent Guide

คู่มือนี้ใช้สำหรับกรอกคอลัมน์ `intent` ใน Google Sheet ให้ตรงกับ logic ที่ระบบรองรับจริงตอนนี้

## หลักสั้น ๆ

- ถ้าไม่แน่ใจ `intent` ให้ปล่อยว่างได้
- ระบบยัง sync และค้นจาก `question / keywords / answer` ได้ตามปกติ
- ควรใส่ `intent` เฉพาะตอนที่ต้องการบังคับคำตอบให้ตรง subtopic มากขึ้น
- อย่าสร้าง intent ใหม่เองสุ่ม ๆ ถ้าโค้ดยังไม่รองรับ

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
- ถ้าอยากได้ intent ใหม่ ให้แจ้งทีม dev ก่อน
