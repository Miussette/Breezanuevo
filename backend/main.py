from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Configuración para servir el frontend de React (Vite) en producción
frontend_path = os.path.join(os.getcwd(), "frontend", "dist")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Maneja tanto los archivos estáticos como las rutas de la SPA."""
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Fallback para index.html si no es un archivo estático (necesario para React Router)
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    return {"error": "Frontend build not found. Run 'npm run build' first."}
