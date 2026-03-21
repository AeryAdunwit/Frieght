# DevOps Guide

คู่มือนี้สรุปของที่เพิ่มไว้เพื่อให้โปรเจกต์พร้อมย้ายไป production ที่เสถียรกว่าเดิม โดยไม่บังคับให้ย้ายของ live ทันที

## 1. Render free tier กับ cold start
- ถ้ายังใช้ free tier จะมี cold start ได้ประมาณ 10-30 วินาที
- ถ้าจะลด latency โดยไม่เปลี่ยนโค้ด:
  - อัปเกรดเป็น paid web service บน Render
  - หรือย้ายไป container service ที่ยังใช้ `uvicorn backend.main:app` เดิม
- ถ้าย้ายแต่ยังใช้ env, domain, build command และ start command เดิม ปกติไม่กระทบ frontend

## 2. Docker
มีไฟล์ใหม่แล้ว:
- `Dockerfile`
- `.dockerignore`

ทดสอบ build ในเครื่อง:

```powershell
docker build -t frieght-backend .
```

รัน local:

```powershell
docker run --rm -p 10000:10000 --env-file backend/.env frieght-backend
```

## 3. Health checks
endpoint ตอนนี้มี:
- `/health`
- `/health/deep`
- `/readyz`

ความต่าง:
- `/health` ใช้สำหรับ liveness เบา ๆ
- `/health/deep` ใช้เช็ก Supabase, Google credentials, Gemini env
- `/readyz` ใช้เป็น readiness check สำหรับ deploy pipeline ได้

## 4. GitHub Actions
workflow ที่มีตอนนี้:
- `.github/workflows/tests.yml`
- `.github/workflows/docker-validate.yml`
- `.github/workflows/render-deploy.yml`
- `.github/workflows/sync.yml`

## 5. Database migrations
เพิ่มโครง migration แล้วที่:
- `supabase/migrations/20260321_000001_initial_schema.sql`

แนวทางใช้งาน:
- ของเก่ายังใช้ `docs/supabase_schema.sql` ได้
- ของใหม่ควรเริ่มใช้ไฟล์ใน `supabase/migrations/`

## 6. Monitoring / Alerting
ขั้นต่ำที่แนะนำ:
- เช็ก `/readyz` จาก uptime monitor ทุก 1-5 นาที
- เปิด Render alerts สำหรับ deploy failure / instance unhealthy
- ใช้ Supabase logs ดู error ฝั่ง DB

ถ้าจะเพิ่มอีกขั้น:
- Sentry หรือ APM สำหรับ backend
- log aggregation แยกจาก stdout
