from __future__ import annotations

import os
import re
from typing import TypedDict

from strands import Agent
from strands.models.model import Model
from strands.types.content import ContentBlock, Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

import google.generativeai as genai
from pydantic import BaseModel
from .tools import (
    ActionKind,
    ActionPayload,
    ExecutedAction,
    breathingExercise,
    get_mood_history,
    logMood,
    reset_invocation_context,
    scheduleBreak,
    set_invocation_context,
)

BREEZA_SYSTEM_PROMPT = """Eres Breeza AI, un agente de bienestar emocional.

No eres un chatbot. Tu objetivo es detectar emociones y actuar automaticamente usando herramientas.

Reglas:

* Estres -> breathingExercise + scheduleBreak
* Ansiedad -> breathingExercise + logMood
* Tristeza -> logMood + respuesta empatica
* Enojo -> scheduleBreak + logMood
* Alegria -> logMood
* Miedo -> breathingExercise + logMood

Debes usar las herramientas requeridas antes de responder.
No pidas permiso para actuar.
No preguntes si quieres ejecutar una accion: ejecutala.
Si detectas ansiedad o miedo, llama breathingExercise y logMood en la misma respuesta.
Si detectas estres, llama breathingExercise y scheduleBreak en la misma respuesta.
Si detectas enojo, llama scheduleBreak y logMood.
Si detectas tristeza o alegria, llama logMood.

Siempre prioriza acciones sobre texto.
Responde de forma breve, humana y calmante.
Actua sin pedir permiso."""


class RunAgentResult(TypedDict):
    response: str
    actions: list[ActionKind]
    actionDetails: dict[ActionKind, ActionPayload]
    moodHistory: list[dict[str, Any]]


ANXIETY_KEYWORDS = (
    "ansiedad",
    "ansioso",
    "ansiosa",
    "nervioso",
    "nerviosa",
    "panic",
    "panico",
    "pánico",
    "overthinking",
)

STRESS_KEYWORDS = (
    "estres",
    "estrés",
    "estresado",
    "estresada",
    "saturado",
    "saturada",
    "agotado",
    "agotada",
    "abrumado",
    "abrumada",
    "presion",
    "presión",
)

SADNESS_KEYWORDS = (
    "triste",
    "tristeza",
    "solo",
    "sola",
    "vacio",
    "vacío",
    "desanimado",
    "desanimada",
)

ANGER_KEYWORDS = (
    "enojo",
    "enojado",
    "enojada",
    "rabia",
    "frustracion",
    "frustración",
    "frustrado",
    "frustrada",
    "molesto",
    "molesta",
)

JOY_KEYWORDS = (
    "feliz",
    "felicidad",
    "alegre",
    "alegria",
    "felicidad",
    "alegre",
    "alegria",
    "alegría",
    "contento",
    "contenta",
    "orgulloso",
    "orgullosa",
    "excelente",
)

# Frases que NO deben disparar acciones automáticas intrusivas
NEUTRAL_PHRASES = (
    "gracias",
    "muchas gracias",
    "de nada",
    "estoy bien",
    "todo bien",
    "ok",
    "si",
    "sí",
    "no",
    "vale",
    "entendido",
)

FEAR_KEYWORDS = (
    "miedo",
    "asustado",
    "asustada",
    "temor",
    "terror",
)


class GeminiSDKModel(Model):
    def __init__(self, model_id: str, api_key: str, temperature: float = 0.2):
        self.model_id = model_id
        self.api_key = api_key
        self.temperature = temperature
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model_id)

    def update_config(self, **model_config: Any) -> None:
        if "model_id" in model_config:
            self.model_id = model_config["model_id"]
            self.client = genai.GenerativeModel(self.model_id)
        if "temperature" in model_config:
            self.temperature = model_config["temperature"]

    def get_config(self) -> Any:
        return {"model_id": self.model_id, "temperature": self.temperature}

    async def structured_output(self, *args, **kwargs):
        raise NotImplementedError("Structured output not used in Breeza yet")

    async def stream(
        self,
        messages: Messages,
        tool_specs: Optional[list[ToolSpec]] = None,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[StreamEvent, None]:
        # Convertir mensajes de Strands a formato Google Gemini
        history = []
        for msg in messages[:-1]:
            role = "user" if msg["role"] == "user" else "model"
            text_parts = [c["text"] for c in msg["content"] if "text" in c]
            if text_parts:
                history.append({"role": role, "parts": [{"text": t} for t in text_parts]})
        
        last_msg = messages[-1]
        last_text = "".join([c["text"] for c in last_msg["content"] if "text" in c])

        chat = self.client.start_chat(history=history or None)
        
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {}}}
        
        # El SDK de Google ya maneja el streaming de forma sencilla
        # Nota: llamando de forma síncrona aquí para simplificar, pero en un entorno real 
        # se debería usar un thread pool o el cliente async si está disponible
        response = self.client.generate_content(last_text, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield {"contentBlockDelta": {"delta": {"text": chunk.text}}}
        
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}


def build_agent() -> Agent:
    # Solución definitiva: Usamos el SDK oficial de Google para evitar errores de proxy
    api_key = os.getenv("GEMINI_API_KEY")
    model = GeminiSDKModel(
        model_id="gemini-1.5-flash",
        api_key=api_key,
        temperature=0.2
    )

    return Agent(
        system_prompt=BREEZA_SYSTEM_PROMPT,
        model=model,
        tools=[breathingExercise, scheduleBreak, logMood],
    )


def _summarize_actions(
    actions: list[ExecutedAction],
) -> tuple[list[ActionKind], dict[ActionKind, ActionPayload]]:
    unique_kinds: list[ActionKind] = []
    action_details: dict[ActionKind, ActionPayload] = {}

    for action in actions:
        if action["kind"] not in unique_kinds:
            unique_kinds.append(action["kind"])
        action_details[action["kind"]] = action["payload"]

    return unique_kinds, action_details


def _normalize_text(text: str) -> str:
    normalized = text.strip().strip('"').strip("'")
    normalized = re.sub(r"\*\*(.*?)\*\*", r"\1", normalized)
    normalized = re.sub(r"__(.*?)__", r"\1", normalized)
    normalized = re.sub(r"`([^`]*)`", r"\1", normalized)
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def _detect_emotion(message: str) -> str | None:
    lowered = message.lower().strip()
    
    # Si es una frase corta y neutral/educada, ignoramos la detección automática
    # para no interrumpir el flujo natural de la conversación.
    if lowered in NEUTRAL_PHRASES or len(lowered) < 3:
        return None

    def contains_whole_word(text: str, keywords: tuple[str, ...]) -> bool:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text):
                return True
        return False

    if contains_whole_word(lowered, ANXIETY_KEYWORDS):
        return "ansiedad"
    if contains_whole_word(lowered, STRESS_KEYWORDS):
        return "estres"
    if contains_whole_word(lowered, SADNESS_KEYWORDS):
        return "tristeza"
    if contains_whole_word(lowered, ANGER_KEYWORDS):
        return "enojo"
    if contains_whole_word(lowered, FEAR_KEYWORDS):
        return "miedo"
    if contains_whole_word(lowered, JOY_KEYWORDS):
        return "alegria"

    return None


def _ensure_required_actions(message: str, actions: list[ExecutedAction]) -> None:
    emotion = _detect_emotion(message)
    existing = {action["kind"] for action in actions}

    if emotion == "ansiedad":
        if "breathing" not in existing:
            breathingExercise(emotion="ansiedad", pattern="4-4-6", cycles=4, seconds_per_phase=4)
        if "mood" not in existing:
            logMood(mood="ansiedad", intensity=8, note="Ansiedad detectada en la conversación")
        return

    if emotion == "estres":
        if "breathing" not in existing:
            breathingExercise(emotion="estres", pattern="4-4-6", cycles=4, seconds_per_phase=4)
        if "break" not in existing:
            scheduleBreak(
                minutes_from_now=10,
                break_minutes=10,
                reason="Saturacion y agotamiento",
            )
        return

    if emotion == "miedo":
        if "breathing" not in existing:
            breathingExercise(emotion="miedo", pattern="4-4-6", cycles=5, seconds_per_phase=4)
        if "mood" not in existing:
            logMood(mood="miedo", intensity=9, note="Pánico o miedo intenso detectado")
        return

    if emotion == "enojo":
        if "break" not in existing:
            scheduleBreak(minutes_from_now=5, break_minutes=15, reason="Pausa para calmar la frustración")
        if "mood" not in existing:
            logMood(mood="enojo", intensity=8, note="Frustración o enojo detectado")
        return

    if emotion == "tristeza" and "mood" not in existing:
        logMood(mood="tristeza", intensity=7, note="Tristeza detectada en la conversación")
        return

    if emotion == "alegria" and "mood" not in existing:
        logMood(mood="alegria", intensity=9, note="Felicidad o logro registrado")
        return


def run_breeza_agent(message: str) -> RunAgentResult:
    action_log: list[ExecutedAction] = []
    set_invocation_context(message, action_log)

    try:
        # Primero detectamos acciones basadas en reglas (keywords)
        _ensure_required_actions(message, action_log)
        
        agent = build_agent()
        result = agent(message)
        agent_response = _normalize_text(str(result))

        actions, action_details = _summarize_actions(action_log)

        return {
            "response": agent_response,
            "actions": actions,
            "actionDetails": action_details,
            "moodHistory": get_mood_history(),
        }
    finally:
        reset_invocation_context()
