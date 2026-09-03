# Elevate AI

Tutor de inglés por voz **100% local** (STT → LLM → TTS) en una **RTX 3060 12GB**. Sin APIs cloud en el camino crítico y sin suscripción.

Pensado para hispanohablantes en torno a **B2**, con estirón suave hacia **C1**.

![Pipeline local Elevate AI](docs/assets/architecture-pipeline.png)

Guía operativa en español. La landing principal (EN) es [`README.md`](README.md). Arquitectura: [`docs/architecture.md`](docs/architecture.md).

## Estado

| Fase | Alcance | Estado |
|------|---------|--------|
| 1 | Inferencia local | **Hecha** |
| 2 | WebSocket + barge-in | **Hecha** |
| 3 | UI React + mic + VAD | **Hecha** (Studio Nocturne gold / night) |
| 4a | Canal dual SPEAK / FEEDBACK | **Hecha** |
| 4b | Memoria SQLite | **Hecha** (`data/elevate.db` + brief) |
| 4c | Shadowing | Pendiente |

Warm batch ~**3.3 s**. Streaming **TTFA ~2.1 s**. Cold start de Ollama ~60–80 s.

**Windows:** no hace falta CUDA Toolkit de sistema. Fijar **`onnxruntime-gpu==1.20.2`**.

## Cómo usar la app

1. Arranca **Ollama** (debe responder en `127.0.0.1:11434`).
2. Arranca el **backend** (`uvicorn` en `:8000`) y el **frontend** (`npm run dev` → [http://localhost:5173](http://localhost:5173)).
3. Elige un **escenario** en el panel izquierdo. Eso sí cambia lo que habla el tutor.
4. **Start Session** y acepta el micrófono.
5. Habla. Tras **~1.5 s** de silencio se envía el turno.
6. Las correcciones salen en **Coach notes**, no en voz. **Esc** interrumpe. Luna / sol cambia Gold ↔ Night.

Nivel guardado: **B2**.

## Cómo encaja Ollama

Ollama es un **servicio aparte**. FastAPI le habla por HTTP; la UI nunca lo llama. Hay que tenerlo abierto **antes** de Start Session.

## Instalación y arranque

Mismos comandos que en [`README.md`](README.md) (venv Python 3.12, torch cu124, `download_models.py`, `npm install`).

```powershell
.\.venv\Scripts\Activate.ps1
$env:Path = "$env:LOCALAPPDATA\Programs\Ollama;" + $env:Path
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
cd frontend
npm run dev
```

| URL | Qué es |
|-----|--------|
| http://localhost:5173 | **App de producto** |
| http://127.0.0.1:8000/ | Demo HTML Fase 2 |

## Canal dual, escenarios y SQLite

- `<<<SPEAK>>>` → TTS + transcript. `<<<FEEDBACK>>>` → sidebar. El TTS no ve JSON.
- El escenario se manda en `CONFIG` y se inyecta al final del system prompt. Cambiarlo a mitad de sesión limpia el historial del turno.
- SQLite (`data/elevate.db`): **solo FastAPI** lee/escribe. Ollama **nunca** ejecuta SQL; recibe un *memory brief* de texto. Detalle: [`docs/architecture.md`](docs/architecture.md) §9.

## Tests

```powershell
.\.venv\Scripts\python.exe tests\test_protocol.py
.\.venv\Scripts\python.exe tests\test_memory.py
```

## Licencia

MIT — [LICENSE](LICENSE).
