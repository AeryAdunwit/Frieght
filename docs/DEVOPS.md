# DevOps Guide

คู่มือนี้สรุปแนวทาง DevOps ของโปรเจกต์ในสถานะปัจจุบัน โดยเน้นว่าเราสามารถเตรียม production readiness ได้ก่อน โดยไม่ต้องกระทบ live ทันที

## 1. Render and Cold Start
- Render free tier อาจมี cold start ประมาณ 10-30 วินาที
- ถ้าต้องการลด latency โดยไม่เปลี่ยนโค้ด:
  - อัปเกรดเป็น paid web service
  - หรือย้ายไป container service โดยใช้ start command เดิม

## 2. Docker
ไฟล์ที่มีแล้ว:
- `Dockerfile`
- `.dockerignore`

คำสั่ง build:
```powershell
docker build -t frieght-backend .
```

คำสั่งรัน local:
```powershell
docker run --rm -p 10000:10000 --env-file backend/.env frieght-backend
```

## 3. Health Checks
endpoint ที่มีแล้ว:
- `/health`
- `/health/deep`
- `/readyz`

การใช้งาน:
- `/health` สำหรับ liveness
- `/health/deep` สำหรับเช็ก dependency หลัก
- `/readyz` สำหรับ readiness ก่อนปล่อย deploy

## 4. CI and Quality Gates
workflow ที่มีแล้ว:
- `.github/workflows/tests.yml`
- `.github/workflows/docker-validate.yml`
- `.github/workflows/render-deploy.yml`
- `.github/workflows/sync.yml`

และมี pre-commit scaffold แล้วที่:
- `.pre-commit-config.yaml`

## 5. Database Migrations
migration หลักที่มีแล้ว:
- `supabase/migrations/20260321_000001_initial_schema.sql`
- `supabase/migrations/20260323_000002_enable_rls_policies.sql`

ถ้าจะเปิด RLS จริง ให้ใช้คู่กับ:
- [SUPABASE_RLS_ROLLOUT.md](./SUPABASE_RLS_ROLLOUT.md)

## 6. Monitoring and Alerting
ขั้นพื้นฐานที่แนะนำ:
- เช็ก `/readyz` จาก uptime monitor
- เปิด Render alerts สำหรับ deploy fail / unhealthy service
- ใช้ Supabase logs และ Render logs ในการ debug

monitoring scaffold ที่มีแล้ว:
- Sentry opt-in ผ่าน env:
  - `SENTRY_DSN`
  - `SENTRY_ENVIRONMENT`
  - `SENTRY_TRACES_SAMPLE_RATE`

ถ้ายังไม่ตั้ง env เหล่านี้ ระบบจะทำงานเหมือนเดิม

## 7. Safe Rollout Principle
ทุก phase ใหม่ควรแยกเป็น 2 ชั้น:
1. เพิ่ม scaffold / tests / docs ก่อน
2. ค่อยเปิดใช้จริงผ่าน env หรือ deploy plan

แนวนี้ช่วยให้พัฒนาได้ต่อเนื่อง โดยไม่ไปชน live ที่ใช้งานอยู่
