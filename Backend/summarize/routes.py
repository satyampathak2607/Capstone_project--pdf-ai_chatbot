from fastapi import APIRouter, HTTPException
import os
import fitz
from transformers import pipeline
from concurrent.futures import ThreadPoolExecutor
import asyncio
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
AI_KEY = os.environ.get("AI_KEY")
print(f"[DEBUG] AI_KEY loaded: {AI_KEY}")
client = OpenAI(
    api_key=os.environ.get("AI_KEY"),
    base_url="https://openrouter.ai/api/v1"
)


summarize_router = APIRouter()
executor = ThreadPoolExecutor(max_workers=4)

summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")



PDF_DIR = os.path.abspath("pdfs")

def get_latest_pdf_file():
    pdf_files = sorted(
        [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")],
        key = lambda x: os.path.getmtime(os.path.join(PDF_DIR, x)),
        reverse=True
    )
    if not pdf_files:
        raise FileNotFoundError("No PDF files found in the directory.")
    return os.path.join(PDF_DIR, pdf_files[0])

def extract_pdf_text(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
         text += page.get_text("text") + "\n" # IGNORE
    return text

def split_into_chunks(text, max_chunk_words=250):
    words = text.split()
    return [" ".join(words[i:i+max_chunk_words]) for i in range(0, len(words), max_chunk_words)]

def summarize_chunks(text):
    if not text or not text.strip():
        return "No text content to summarize."

    chunks = split_into_chunks(text)
    summaries = []

    MAX_CHUNKS = 15
    for i, chunk in enumerate(chunks[:MAX_CHUNKS]):
        if len(chunk.strip()) < 50:
            continue
        try:
            result = summarizer(
                chunk,
                max_length=min(150, int(len(chunk.split()) * 0.8)),
                min_length=40,
                truncation=True,
                do_sample=False
            )
            if isinstance(result, list) and len(result) > 0:
                summary_dict = result[0]
                if isinstance(summary_dict, dict) and "summary_text" in summary_dict:
                    summaries.append(summary_dict["summary_text"])
        except Exception as e:
            print(f"Failed to summarize chunk {i + 1}: {e}")
            continue

    if not summaries:
        return "Unable to generate summary from the provided text."

    return summaries
    

async def run_in_threadpool(func, *args):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, lambda: func(*args))



@summarize_router.post("/summarize")
async def summarize_pdf():
    try:
        pdf_path = await run_in_threadpool(get_latest_pdf_file)
        print(f"[DEBUG] PDF path: {pdf_path}")
        raw_text = await run_in_threadpool(extract_pdf_text, pdf_path)
        print(f"[DEBUG] Extracted {len(raw_text)} characters")
        summaries = await run_in_threadpool(summarize_chunks, raw_text)

        print(f"[DEBUG] Generated {len(summaries)} raw summaries")

        
        if isinstance(summaries, str):
            summaries = [summaries]

        summaries = [s["summary_text"] if isinstance(s, dict) and "summary_text" in s else str(s) for s in summaries]

        print(f"[DEBUG] Cleaned to {len(summaries)} summaries")

        
        import json
        SUMMARY_FILE = os.path.join("Backend", "summarize", "last_summary.json")
        os.makedirs(os.path.dirname(SUMMARY_FILE), exist_ok=True)
        with open(SUMMARY_FILE, "w") as f:
            json.dump(summaries, f)

        print(f"[✅] Saved summaries to {SUMMARY_FILE}")

        return {"pdf": os.path.basename(pdf_path), "summaries": summaries}

    except Exception as e:
        print(f"[❌] Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

