# Setup Google Sheets -> Supabase -> Render

คู่มือนี้ใช้สำหรับตั้งค่าระบบ knowledge base ให้พร้อมใช้งานจริงแบบทีละขั้น

## 1. จัด Google Sheet

ทุกแท็บให้ใช้หัวคอลัมน์นี้:

```text
question | answer | keywords | intent | active
```

แท็บที่ควรมี:
- `solar`
- `pricing`
- `booking`
- `claim`
- `coverage`
- `documents`
- `timeline`
- `general`

ถ้าต้องการข้อมูลตัวอย่างพร้อมวาง:
- ดูที่ [GOOGLE_SHEETS_PASTE_READY.md](/C:/Users/Sorravit_L/Frieght/docs/GOOGLE_SHEETS_PASTE_READY.md)
- ดูรายการ `intent` ที่รองรับจริงที่ [GOOGLE_SHEETS_INTENT_GUIDE.md](/C:/Users/Sorravit_L/Frieght/docs/GOOGLE_SHEETS_INTENT_GUIDE.md)

## 2. รัน SQL ใน Supabase

ไปที่ `SQL Editor` แล้วรันไฟล์นี้:
- [supabase_schema.sql](/C:/Users/Sorravit_L/Frieght/docs/supabase_schema.sql)

ถ้าเคยมี table เดิมอยู่แล้ว อย่างน้อยต้องมี:

```sql
alter table knowledge_base
  add column if not exists intent text;
```

แล้วอัปเดต RPC:

```sql
create or replace function match_knowledge(
  query_embedding vector(768),
  match_count int,
  match_threshold float
)
returns table (
  id text,
  topic text,
  question text,
  answer text,
  intent text,
  similarity float
)
language sql
stable
as $$
  select
    id,
    topic,
    question,
    answer,
    intent,
    1 - (embedding <=> query_embedding) as similarity
  from knowledge_base
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;
```

## 3. เช็ก env ในเครื่องหรือ Render

ต้องมีค่าอย่างน้อย:
- `GEMINI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SHEET_ID`
- `GOOGLE_CREDENTIALS`
- `EMBEDDING_MODEL=models/gemini-embedding-001`

## 4. Sync ข้อมูลจาก Google Sheet เข้า Supabase

รันจาก root ของโปรเจกต์:

```powershell
python -m backend.sync_vectors
```

ถ้าต้องการสร้างแท็บและใส่ข้อมูลตัวอย่างอัตโนมัติ:

```powershell
python -m backend.seed_knowledge
```

ถ้าต้องการสร้างแท็บคู่มือ `intent_guide` สำหรับทีมใช้อ้างอิงเรื่อง `intent` และ `intent family`
โดยไม่ให้ถูก sync เข้า knowledge base:

```powershell
python -m backend.seed_intent_guide
```

หมายเหตุ:
- ตอนนี้ `seed_knowledge.py` รองรับ header ใหม่ที่มี `intent` แล้ว
- ถ้าข้อมูลใน Google Sheet เป็นข้อมูลจริงอยู่แล้ว ให้ใช้ `sync_vectors` อย่างเดียว
- `intent_guide` ใช้หัวตารางคนละแบบกับ knowledge tabs จึงไม่ถูกรวมตอน `sync knowledge`

## 5. เช็กใน Supabase ว่าข้อมูลเข้าแล้ว

รันใน `SQL Editor`:

```sql
select count(*) from knowledge_base;
```

```sql
select topic, count(*) from knowledge_base group by topic order by topic;
```

ควรเห็น row ของหมวด:
- `solar`
- `pricing`
- `booking`
- `claim`
- `coverage`
- `documents`
- `timeline`
- `general`

## 6. Redeploy Render

หลัง sync เสร็จ ให้ redeploy Render 1 รอบ เพื่อให้ backend ใช้ data ล่าสุด

แนะนำ:
- `Manual Deploy`
- `Clear build cache & deploy`

## 7. คำถามที่ควรใช้ทดสอบ

### Solar
- `บริการส่ง Solar ผ่าน Hub คืออะไร`
- `Solar ผ่าน Hub คิดราคายังไง`
- `ต้องเตรียมข้อมูลอะไรบ้าง`

### Coverage
- `ส่งได้ทั่วประเทศไหม`
- `มีส่งต่างจังหวัดไหม`

### Documents
- `ต้องใช้เอกสารอะไรบ้าง`
- `ต้องใช้ POD หรือไม่`

### Timeline
- `ปกติใช้เวลากี่วัน`
- `ตัดรอบกี่โมง`

## 8. ถ้ายังตอบกว้างเกินไป

ให้แก้ที่ Google Sheet ก่อนเป็นลำดับแรก:
- แยก 1 แถวต่อ 1 คำถาม
- ลดคำตอบยาว ๆ
- เพิ่ม `keywords` เป็นวลี
- เพิ่ม `intent` ให้ชัด

ถ้ายังไม่คมพอ:
- ลดจำนวน row ที่ดึงมาใน retrieval
- หรือทำ direct reply สำหรับ intent ที่ชัดมาก เช่น `coverage`, `documents`, `timeline`
