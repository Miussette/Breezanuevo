from __future__ import annotations

import os
import re
from typing import TypedDict

from strands import Agent
from strands.models.model import Model
from strands.types.content import ContentBlock, Messages
from strands.types.streaming import StreamEvent
from strands.types.tools import ToolSpec

from google import genai
from google.genai import types
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
        self.client = genai.Client(api_key=api_key)
        # Lista de modelos de respaldo en orden de prioridad
        self.fallback_models = [
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro-latest",
            "gemini-2.0-flash-exp" # Último recurso
        ]

    def update_config(self, **model_config: Any) -> None:
        if "model_id" in model_config:
            self.model_id = model_config["model_id"]
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
        # Convertir mensajes de Strands a formato Google Gemini API
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            text_parts = [c["text"] for c in msg["content"] if "text" in c]
            if text_parts:
                contents.append(types.Content(role=role, parts=[types.Part(text=t) for t in text_parts]))
        
        yield {"messageStart": {"role": "assistant"}}
        yield {"contentBlockStart": {"start": {}}}
        
        # Intentamos con la cadena de modelos
        models_to_try = [self.model_id] + [m for m in self.fallback_models if m != self.model_id]
        
        has_content = False
        last_exception = None
        
        for model in models_to_try:
            try:
                print(f"DEBUG AI: Intentando con {model}...")
                
                # Configuración de seguridad relajada
                safety_settings = [
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]

                response = await self.client.aio.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=self.temperature,
                        safety_settings=safety_settings,
                    )
                )
                
                async for chunk in response:
                    if chunk.text:
                        has_content = True
                        yield {"contentBlockDelta": {"delta": {"text": chunk.text}}}
                
                if has_content:
                    break # Éxito con este modelo
                    
            except Exception as e:
                last_exception = e
                print(f"DEBUG AI: Error con {model}: {str(e)[:100]}")
                # Si es un error de cuota o servicio, intentamos el siguiente
                if any(x in str(e) for x in ["429", "503", "504", "SERVICE_UNAVAILABLE"]):
                    continue
                else:
                    # Otros errores (como 404 o 400) también intentamos el siguiente por si acaso
                    continue
        
        if not has_content:
            fallback_text = (
                "\n\n[Breeza: Misión de Calma Activa]\n"
                "Google Gemini está saturado, pero yo sigo aquí contigo. \n"
                "Respiremos juntos mientras vuelve la conexión:\n"
                "1. Inhala profundo por la nariz contando 4 segundos.\n"
                "2. Mantén el aire por 4 segundos más.\n"
                "3. Exhala muy lento por la boca durante 6 segundos.\n"
                "Repite esto mientras presionas los botones de abajo. Todo va a estar bien."
            )
            yield {"contentBlockDelta": {"delta": {"text": fallback_text}}}
        
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": "end_turn"}}


def build_agent() -> Agent:
    # Usamos gemini-flash-latest que es el alias más compatible
    api_key = os.getenv("GEMINI_API_KEY")
    model = GeminiSDKModel(
        model_id="gemini-flash-latest",
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
