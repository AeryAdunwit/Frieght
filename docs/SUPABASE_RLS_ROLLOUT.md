# Supabase RLS Rollout

คู่มือนี้ใช้สำหรับเปิด `Row Level Security (RLS)` แบบค่อยเป็นค่อยไป โดยไม่ทำให้ของ live สะดุด

## เป้าหมาย
- ปิดการเข้าถึงตาราง operational จาก `anon` และ `authenticated`
- ให้ backend ใช้ `SUPABASE_SERVICE_KEY` ต่อไปเหมือนเดิม
- ลดความเสี่ยงกรณี key ฝั่ง client ถูกใช้ query ตารางสำคัญโดยตรง

## ไฟล์ migration
- [20260323_000002_enable_rls_policies.sql](/C:/Users/Sorravit_L/Frieght/supabase/migrations/20260323_000002_enable_rls_policies.sql)

## สิ่งที่ migration นี้ทำ
- เปิด RLS ให้ตารางหลักทั้งหมด
- revoke สิทธิ์ `anon` และ `authenticated` ออกจากตาราง operational
- ใส่ deny-all policies สำหรับ:
  - `site_metrics`
  - `site_visitors`
  - `chat_logs`
  - `chat_log_reviews`
  - `chat_feedback`
  - `sheet_approvals`
  - `handoff_requests`
  - `knowledge_sync_runs`
- เตรียม scaffold policy สำหรับ `knowledge_base`

## ทำไมยังปลอดภัยกับโค้ดปัจจุบัน
- backend ใช้ service-role key เป็นหลัก
- service role bypass RLS ได้
- frontend ปัจจุบันไม่ได้ query Supabase table เหล่านี้ตรง ๆ

## ขั้นตอน rollout ที่แนะนำ
1. ตรวจว่า Render ยังตั้ง `SUPABASE_SERVICE_KEY` อยู่ครบ
2. เช็ก `/health/deep` ให้ผ่านก่อน
3. เปิด Supabase SQL Editor
4. รัน migration นี้ใน environment ที่ไม่ใช่ production ก่อน
5. ทดสอบ:
   - chatbot ตอบปกติ
   - `/analytics/chat-overview` ปกติ
   - `/analytics/visit` ปกติ
   - knowledge sync ปกติ
6. ถ้าผ่านค่อยรันใน production

## checklist หลังเปิดจริง
- `GET /health/deep` ยัง `ok`
- chat flow ปกติ
- handoff ปกติ
- analytics/admin ปกติ
- knowledge sync ปกติ
- tracking ปกติ

## ถ้าต้อง rollback
- ปิด RLS เป็นรายตาราง หรือ drop policy ที่เพิ่งเพิ่ม
- เพราะ migration นี้แยกไฟล์ไว้ชัด จึงย้อนกลับได้ง่าย

## หมายเหตุ
- policy `knowledge_base` ถูก scaffold ไว้แต่ยังเป็น deny-default
- ถ้าอนาคตมี frontend ที่อ่าน knowledge จาก Supabase ตรง ๆ ค่อยออกแบบ policy read-only ใหม่แบบเฉพาะ use case
