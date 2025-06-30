from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, json
from openai import OpenAI
from dotenv import load_dotenv

chat_router = APIRouter()
load_dotenv()

AI_KEY = os.getenv("AI_KEY")
if not AI_KEY:
    raise ValueError("❌ AI_KEY not found")
print(f"[DEBUG] Loaded AI_KEY? {'Yes' if AI_KEY else 'No'}")



client = OpenAI(
    api_key=AI_KEY,
    base_url="https://openrouter.ai/api/v1"
)

SUMMARY_FILE = os.path.join("Backend", "summarize", "last_summary.json")

class ChatRequest(BaseModel):
    question: str

@chat_router.post("/chat")
async def chat_with_pdf(req: ChatRequest):
    try:
        if not os.path.exists(SUMMARY_FILE):
            raise HTTPException(status_code=404, detail="No summary available.")

        with open(SUMMARY_FILE, "r") as f:
            summaries = json.load(f)

        combined_context = " ".join(summaries)
        prompt = f"Answer the question using the context below:\n\nContext:\n{combined_context}\n\nQuestion: {req.question}"

        response = client.chat.completions.create(
             model="mistralai/mistral-7b-instruct:v0.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on PDF content."},
                {"role": "user", "content": prompt}
            ]
        )

        return {"answer": response.choices[0].message.content.strip()}

    except Exception as e:
        print(f"[❌] Chat failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
