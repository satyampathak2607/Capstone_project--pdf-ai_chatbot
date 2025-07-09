from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio

upload_router = APIRouter()
executor = ThreadPoolExecutor(max_workers=2)

UPLOAD_DIR = os.path.abspath("pdfs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_pdf_file(file: UploadFile, save_path: str):
    try:
        print(f"[Saving] Path: {save_path}")
        file.file.seek(0) 
        with open(save_path, "wb") as f:
            f.write(file.file.read())
        print("[✅] File saved successfully.")
    except Exception as e:
        print(f"[❌] Error while saving: {e}")
        raise e

async def run_in_threadpool(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))

@upload_router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        file_id = str(uuid.uuid4())
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

        await run_in_threadpool(save_pdf_file, file, save_path)

        return {"message": "PDF uploaded successfully", "filename": save_path}

    except Exception as e:
        print(f"[❌] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
