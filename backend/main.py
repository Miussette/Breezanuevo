from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .agent import run_breeza_agent
from .tools import get_mood_history

load_dotenv()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


app = FastAPI(title="Breeza AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "breeza-ai-backend",
        "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
    }


@app.get("/moods")
def moods() -> dict[str, list[dict[str, object]]]:
    return {"moods": get_mood_history()}


@app.post("/chat")
def chat(payload: ChatRequest) -> dict[str, object]:
    try:
        return run_breeza_agent(payload.message.strip())
    except Exception as exc:  # pragma: no cover - simple demo API path
        raise HTTPException(status_code=500, detail=str(exc)) from exc
