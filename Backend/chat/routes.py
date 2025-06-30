from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import openai
from dotenv import load_dotenv

chat_router = APIRouter()
load_dotenv()
AI_KEY = os.environ.get("AI_KEY")
print(f"[DEBUG] AI_KEY loaded: {AI_KEY}")
openai.api_key = AI_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# Path to summary file saved after /summarize
SUMMARY_FILE = os.path.join("Backend", "summarize", "last_summary.json")

class ChatRequest(BaseModel):
    question: str

@chat_router.post("/chat")
async def chat_with_pdf(req: ChatRequest):
    try:
        if not os.path.exists(SUMMARY_FILE):
            raise HTTPException(status_code=404, detail="No summary available yet. Please summarize a PDF first.")

        with open(SUMMARY_FILE, "r") as f:
            summaries = json.load(f)

        combined_context = " ".join(summaries)
        prompt = f"Answer the following question using the provided context.\n\nContext:\n{combined_context}\n\nQuestion: {req.question}"

        response = openai.ChatCompletion.create(
            model="mistralai/Mistral-7B-Instruct-v0.2", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on PDF content."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response["choices"][0]["message"]["content"]
        return {"answer": answer.strip()}

    except Exception as e:
        print(f"[❌] Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
