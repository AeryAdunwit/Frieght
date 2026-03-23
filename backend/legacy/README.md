## Legacy Backend Snapshot

โฟลเดอร์นี้เก็บ snapshot ของ backend รุ่นเก่าไว้สำหรับอ้างอิงย้อนหลังเท่านั้น

สถานะปัจจุบัน:
- runtime ที่ใช้งานจริงอยู่ที่ `backend/main.py`
- scaffold ใหม่อยู่ที่ `backend/app/`
- route หลัก (`chat`, `analytics`, `tracking`, `health`, `handoff`, `knowledge-admin`) ถูกย้ายไปก้อน `backend/app/routers/` แล้ว

ข้อสำคัญ:
- ห้ามเพิ่ม feature ใหม่ในโฟลเดอร์นี้
- ห้ามชี้ Render start command มาที่ไฟล์ใน `backend/legacy/`
- ถ้าจะลบโฟลเดอร์นี้ ให้ทำหลังจาก parity check และ deploy ของก้อน `backend/app/` ผ่านครบแล้ว

เป้าหมาย:
- ใช้เป็นจุดพักระหว่าง refactor
- ล้างออกจาก repo เมื่อเลิกพึ่ง root-level legacy code ได้ครบ
