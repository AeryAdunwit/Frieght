# Testing Guide

คู่มือสั้น ๆ สำหรับทีมในการรัน test ของโปรเจกต์นี้แบบไม่กระทบของ live

## สิ่งที่มีตอนนี้
- Backend unit tests
- Backend API smoke tests
- Frontend syntax smoke check
- GitHub Actions workflow สำหรับรันอัตโนมัติ

## รันทั้งหมดในเครื่อง
จาก root ของโปรเจกต์ ใช้คำสั่งนี้:

```powershell
py -3 -m unittest discover -s backend/tests -v
```

ถ้าเครื่องไม่มี `py` แต่มี `python`:

```powershell
python -m unittest discover -s backend/tests -v
```

## รันเฉพาะไฟล์
เช็ก tracking:

```powershell
py -3 -m unittest backend.tests.test_tracking -v
```

เช็ก sanitizer:

```powershell
py -3 -m unittest backend.tests.test_sanitizer -v
```

เช็ก intent router:

```powershell
py -3 -m unittest backend.tests.test_intent_router -v
```

เช็ก API smoke:

```powershell
py -3 -m unittest backend.tests.test_api_smoke -v
```

## เช็ก frontend แบบเร็ว

```powershell
node --check Frieght/js/chat.js
```

คำสั่งนี้ไม่รันหน้าเว็บ แต่ช่วยจับ syntax error ในไฟล์แชตหลักได้

## ไฟล์ test ปัจจุบัน
- `backend/tests/test_tracking.py`
- `backend/tests/test_sanitizer.py`
- `backend/tests/test_intent_router.py`
- `backend/tests/test_security_service.py`
- `backend/tests/test_math_quick_reply.py`
- `backend/tests/test_api_smoke.py`

## ดูผลบน GitHub Actions
workflow ที่ใช้คือ:

- `.github/workflows/tests.yml`

มันจะรันเมื่อ:
- push
- pull request
- workflow_dispatch

## ถ้า test fail ให้ดูอะไร
1. ดูชื่อไฟล์ test ที่ fail ก่อน
2. ดูชื่อเคส test ที่ fail
3. ดู traceback บรรทัดท้าย ๆ
4. ถ้าเป็น API smoke test ให้เช็กว่ามีการเปลี่ยน route หรือ config หรือไม่

## แนวทางใช้งานในทีม
- ก่อน push งาน backend ให้รัน test อย่างน้อย 1 รอบ
- ถ้าแก้หน้าแชต ให้รัน `node --check Frieght/js/chat.js`
- ถ้าแก้ route หรือ helper สำคัญ ให้เพิ่ม test ตามไฟล์ที่แก้
- อย่าแก้ test ให้ผ่านโดยไม่เข้าใจ behavior จริงของระบบ
