import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai
from supabase import create_client
import json
import time
from dotenv import load_dotenv

load_dotenv()

SHEET_ID   = os.environ.get('SHEET_ID')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY') # ใช้ Service key เพื่อให้สามารถเขียนข้อมูลได้
GEMINI_KEY   = os.environ.get('GEMINI_API_KEY')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def get_sheets_data() -> list[dict]:
    creds_info_str = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_info_str:
        print("Missing GOOGLE_CREDENTIALS environment variable.")
        return []
        
    try:
        creds_info = json.loads(creds_info_str)
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=creds)
        meta = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        
        all_rows = []
        for sheet in meta.get('sheets', []):
            topic = sheet['properties']['title']
            result = service.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'{topic}'!A:E" # ดึงคอลัมน์ A ถึง E
            ).execute()
            values = result.get('values', [])
            if len(values) < 2:
                continue
            
            headers = [h.lower().strip() for h in values[0]]
            for i, row in enumerate(values[1:]):
                entry = {'topic': topic, 'row_index': i}
                for j, h in enumerate(headers):
                    entry[h] = row[j].strip() if j < len(row) else ''
                
                # ข้ามถ้าไม่ได้ตั้งค่า active ไว้ หรือตั้งเป็น no
                if entry.get('active', '').lower() == 'no':
                    continue
                if entry.get('question') and entry.get('answer'):
                    all_rows.append(entry)
        return all_rows
    except Exception as e:
        print(f"Error fetching sheets data: {e}")
        return []

def embed_batch(texts: list[str]) -> list[list[float]]:
    genai.configure(api_key=GEMINI_KEY)
    embeddings = []
    for text in texts:
        try:
            result = genai.embed_content(
                model='models/text-embedding-004',
                content=text
            )
            embeddings.append(result['embedding'])
            time.sleep(0.1)   # Respect API rate limit
        except Exception as e:
            print(f"Error embedding text: {e}")
            embeddings.append([]) # Append empty to keep length consistent
    return embeddings

def sync():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Missing SUPABASE credentials. Sync aborted.")
        return
        
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    rows = get_sheets_data()
    print(f'Syncing {len(rows)} rows...')

    for row in rows:
        content = f"Q: {row['question']}\nA: {row['answer']}"
        row_id  = f"{row['topic']}_{row['row_index']}"
        
        embeddings = embed_batch([content])
        if not embeddings or not embeddings[0]:
            continue
            
        embedding = embeddings[0]
        
        try:
            supabase.table('knowledge_base').upsert({
                'id':        row_id,
                'topic':     row['topic'],
                'question':  row['question'],
                'answer':    row['answer'],
                'content':   content,
                'embedding': embedding,
            }).execute()
        except Exception as e:
            print(f"Error saving to Supabase for {row_id}: {e}")

    print(f'Done. {len(rows)} rows synced to Supabase.')

if __name__ == '__main__':
    sync()
