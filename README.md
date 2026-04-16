# Breeza AI

Breeza AI es una app full-stack para hackathon con un frontend en React y un backend en Python que usa Strands Agents + Ollama para soporte emocional accionable. El agente detecta estres, ansiedad o tristeza y decide por si mismo cuando activar respiracion, sugerir una pausa o guardar un mood.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Agente: Strands Agents SDK + Ollama
- Voz: Web Speech API + SpeechSynthesis

## Estructura

```text
.
├── backend/
│   ├── __init__.py
│   ├── agent.py
│   ├── main.py
│   ├── requirements.txt
│   └── tools.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite-env.d.ts
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── types.ts
│       ├── components/
│       ├── hooks/
│       └── styles/
└── package.json
```

## Requisitos

- Node.js 20+
- Python 3.11+
- Ollama instalado y ejecutandose localmente

## Paso a Paso

1. Instala dependencias del frontend y scripts raiz:

```bash
npm install
```

2. Crea y activa un entorno virtual para Python:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Instala dependencias del backend:

```bash
python -m pip install -r backend/requirements.txt
```

4. Configura los archivos `.env`:

- Copia `backend/.env.example` a `backend/.env`
- Copia `frontend/.env.example` a `frontend/.env`

5. Levanta Ollama y descarga un modelo:

```bash
ollama serve
ollama pull llama3.1
```

6. Inicia la app completa:

```bash
npm run dev
```

7. Abre el frontend:

```text
http://localhost:5173
```

## Variables De Entorno

### Backend

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
PORT=8787
```

### Frontend

```env
VITE_API_URL=http://localhost:8787
```

## API

### `POST /chat`

Body:

```json
{
  "message": "Me siento muy ansioso con el trabajo"
}
```

Response:

```json
{
  "response": "Respira conmigo. Ya active una pausa breve para bajar la tension.",
  "actions": ["breathing", "break"],
  "actionDetails": {
    "breathing": {
      "action": "breathing",
      "pattern": "4-4-6",
      "cycles": 4,
      "secondsPerPhase": 4,
      "guidance": "Inhala 4, sosten 4, exhala 6.",
      "emotion": "ansiedad"
    }
  },
  "moodHistory": []
}
```

## Comandos Utiles

```bash
npm run dev
npm run build
python -m uvicorn backend.main:app --reload --port 8787
```

## Notas

- El historial emocional se mantiene en memoria para la demo.
- El audio relajante se genera con Web Audio API, sin assets externos.
- La calidad del tool calling depende del modelo local que uses en Ollama.
- Si `llama3.1` te resulta pesado, puedes probar otro modelo local, pero el comportamiento del agente puede variar.
