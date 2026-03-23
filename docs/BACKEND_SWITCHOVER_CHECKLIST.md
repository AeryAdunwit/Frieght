# Backend Switchover Checklist

Checklist นี้มีไว้สำหรับ “วันสลับ runtime จริง” จาก:

- ปัจจุบัน: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- เป้าหมาย: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

เอกสารนี้ตั้งใจให้ใช้หลัง parity ของโครง `backend/app/` ผ่านครบแล้วเท่านั้น
และไม่จำเป็นต้องทำระหว่างที่ live กำลังนิ่งอยู่

## 1. ก่อนสลับ
- `backend/main.py` ต้องเหลือเป็น compatibility bridge เท่านั้น
- root-level helper files (`intent_router.py`, `sanitizer.py`, `vector_search.py`, `tracking.py`, `sheets_loader.py`, `sync_vectors.py`) ต้องเป็น wrapper ทั้งหมด
- tests เหล่านี้ควรผ่าน
  - `backend.tests.test_api_smoke`
  - `backend.tests.test_app_main`
  - `backend.tests.test_main_compat`
  - `backend.tests.test_root_wrappers`

## 2. สิ่งที่ต้องเช็กใน staging / local
- `GET /health` ตอบ `200`
- `GET /health/deep` ตอบ `200`
- `GET /readyz` ตอบ `200`
- `/chat` ยังตอบได้ทั้ง
  - คำถามทั่วไป
  - tracking
  - math quick reply
- `/analytics/chat-overview` ยังตอบได้
- `/tracking/porlor/search` ยังเปิดได้
- `/public-config` ยังตอบได้

## 3. ขั้นตอนสลับ
1. เปลี่ยน start command ใน Render เป็น:
   - `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
2. `Clear build cache & deploy`
3. เช็ก endpoint สำคัญทันที
4. ลองหน้าแชตจริง
5. ลองหน้าแอดมินจริง

## 4. Rollback plan
ถ้ามี regression:
1. เปลี่ยน start command กลับเป็น
   - `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
2. redeploy อีกครั้ง

## 5. หลังสลับสำเร็จ
- อัปเดต `render.yaml`
- อัปเดต `Dockerfile`
- อัปเดต `README.md`
- ค่อยพิจารณาลด root-level wrappers ที่ไม่จำเป็นออกในรอบถัดไป
- ถ้ายังมี legacy ฝั่ง frontend ค้างอยู่ ให้ล้างหลัง parity check เหมือนกัน
