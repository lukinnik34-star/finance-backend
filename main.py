import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

class ChatIn(BaseModel):
    message: str
    system: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/chat")
async def chat(payload: ChatIn):
    if not GEMINI_API_KEY:
        return {"text": "Ошибка: GEMINI_API_KEY не задан на сервере."}

    system_prompt = payload.system or "Ты финансовый ассистент. Отвечай по-русски, кратко."

    # Combine system + user message for Gemini
    full_prompt = f"{system_prompt}\n\nПользователь: {payload.message}"

    try:
        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
                headers={"content-type": "application/json"},
                json={
                    "contents": [
                        {"role": "user", "parts": [{"text": full_prompt}]}
                    ],
                    "generationConfig": {
                        "maxOutputTokens": 1024,
                        "temperature": 0.7
                    }
                }
            )
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {"text": text}

    except Exception as e:
        return {"text": "", "error": str(e)}
