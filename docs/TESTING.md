# Testing Guide

คู่มือสั้น ๆ สำหรับทีมในการรัน test และ quality checks ของโปรเจกต์นี้โดยไม่กระทบของ live

## รัน unittest เดิมทั้งหมด

```powershell
py -3 -m unittest discover -s backend/tests -v
```

ถ้าเครื่องไม่มี `py` แต่มี `python`:

```powershell
python -m unittest discover -s backend/tests -v
```

## รัน pytest พร้อม coverage gate

ติดตั้ง dev tools:

```powershell
py -3 -m pip install -r requirements-dev.txt
```

รัน pytest:

```powershell
py -3 -m pytest
```

ตอนนี้ coverage gate ตั้งขั้นต่ำ `70%` สำหรับ refactored app core ที่เริ่มนิ่งแล้ว

## รันเฉพาะบางไฟล์

```powershell
py -3 -m unittest backend.tests.test_tracking -v
py -3 -m unittest backend.tests.test_api_smoke -v
py -3 -m unittest backend.tests.test_admin_auth_integration -v
```

## Frontend Syntax Smoke Check

```powershell
node --check Frieght/js/chat.js
node --check Frieght/js/chat-network-utils.js
node --check Frieght/js/chat-boot-utils.js
```

## Quality Checks

Ruff:

```powershell
py -3 -m ruff check backend/app backend/tests
```

Mypy:

```powershell
py -3 -m mypy
```

## GitHub Actions

workflow ที่ใช้คือ:

- `.github/workflows/tests.yml`

CI ตอนนี้จะรัน:

- `pytest-cov`
- `ruff`
- `mypy`
- frontend syntax smoke

## ถ้า test fail ให้ไล่ดูอะไร

1. ดูชื่อไฟล์ test ที่ fail ก่อน
2. ดูชื่อเคสที่ fail
3. ดู traceback บรรทัดท้าย ๆ
4. ถ้าเป็น route หรือ auth test ให้เช็ก env/config ที่ patch ใน test ด้วย
