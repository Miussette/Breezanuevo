from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Literal, TypedDict
from uuid import uuid4

from strands import tool

ActionKind = Literal["breathing", "break", "mood"]


class MoodEntry(TypedDict):
    id: str
    mood: str
    intensity: int
    note: str
    capturedText: str
    timestamp: str


class BreathingActionPayload(TypedDict):
    action: Literal["breathing"]
    pattern: str
    cycles: int
    secondsPerPhase: int
    guidance: str
    emotion: str


class BreakActionPayload(TypedDict):
    action: Literal["break"]
    breakAt: str
    breakMinutes: int
    reason: str


class MoodActionPayload(TypedDict):
    action: Literal["mood"]
    saved: bool
    entry: MoodEntry


ActionPayload = BreathingActionPayload | BreakActionPayload | MoodActionPayload


class ExecutedAction(TypedDict):
    kind: ActionKind
    payload: ActionPayload


_mood_history: list[MoodEntry] = []
_mood_lock = Lock()
_invocation_lock = Lock()
_current_source_message = ""
_current_action_log: list[ExecutedAction] | None = None


def set_invocation_context(source_message: str, action_log: list[ExecutedAction]) -> None:
    global _current_source_message, _current_action_log
    _invocation_lock.acquire()
    _current_source_message = source_message
    _current_action_log = action_log


def reset_invocation_context() -> None:
    global _current_source_message, _current_action_log
    _current_source_message = ""
    _current_action_log = None
    _invocation_lock.release()


def _append_action(action: ExecutedAction) -> None:
    if _current_action_log is not None:
        _current_action_log.append(action)


def get_mood_history() -> list[MoodEntry]:
    with _mood_lock:
        return list(reversed(_mood_history))


@tool
def breathingExercise(
    emotion: str = "estres",
    pattern: str = "4-4-6",
    cycles: int = 4,
    seconds_per_phase: int = 4,
) -> BreathingActionPayload:
    """
    Activa una respiracion guiada para bajar estres o ansiedad.

    Args:
        emotion: Emocion detectada en el usuario.
        pattern: Patron sugerido, por ejemplo 4-4-6.
        cycles: Cantidad de ciclos sugeridos.
        seconds_per_phase: Segundos de inhalacion y retencion.
    """
    seconds_per_phase = max(3, min(seconds_per_phase, 8))
    cycles = max(2, min(cycles, 8))

    inhala = seconds_per_phase
    sosten = seconds_per_phase
    exhala = max(seconds_per_phase + 2, 6)
    dynamic_pattern = f"{inhala}-{sosten}-{exhala}"

    payload: BreathingActionPayload = {
        "action": "breathing",
        "pattern": dynamic_pattern,
        "cycles": cycles,
        "secondsPerPhase": seconds_per_phase,
        "guidance": f"Inhala {inhala}, sosten {sosten}, exhala {exhala}.",
        "emotion": emotion,
    }

    _append_action({"kind": "breathing", "payload": payload})

    return payload


@tool
def scheduleBreak(
    minutes_from_now: int = 10,
    break_minutes: int = 5,
    reason: str = "Reducir tension emocional y recuperar foco",
) -> BreakActionPayload:
    """
    Programa una pausa breve cuando detectes estres o saturacion.

    Args:
        minutes_from_now: Minutos hasta comenzar la pausa.
        break_minutes: Duracion de la pausa.
        reason: Motivo de la pausa.
    """
    minutes_from_now = max(1, min(minutes_from_now, 120))
    break_minutes = max(1, min(break_minutes, 30))

    payload: BreakActionPayload = {
        "action": "break",
        "breakAt": (
            datetime.now(timezone.utc) + timedelta(minutes=minutes_from_now)
        ).isoformat(),
        "breakMinutes": break_minutes,
        "reason": reason,
    }

    _append_action({"kind": "break", "payload": payload})

    return payload


@tool
def logMood(
    mood: str,
    intensity: int = 6,
    note: str = "Registro emocional automatico generado por Breeza AI",
) -> MoodActionPayload:
    """
    Guarda un registro emocional cuando detectes ansiedad o tristeza.

    Args:
        mood: Estado emocional principal detectado.
        intensity: Intensidad del 1 al 10.
        note: Nota corta para el historial.
    """
    source_message = _current_source_message

    entry: MoodEntry = {
        "id": str(uuid4()),
        "mood": mood,
        "intensity": max(1, min(intensity, 10)),
        "note": note,
        "capturedText": source_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with _mood_lock:
        _mood_history.append(entry)

    payload: MoodActionPayload = {
        "action": "mood",
        "saved": True,
        "entry": entry,
    }

    _append_action({"kind": "mood", "payload": payload})

    return payload
