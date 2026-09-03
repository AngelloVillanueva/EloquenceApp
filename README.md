# Elevate AI

**100% local English voice tutor** — STT → LLM → TTS on a single NVIDIA RTX 3060 12GB. No cloud APIs on the critical path, no subscription.

Built for Spanish speakers at about **B2**, stretching toward **C1** professional fluency.

![Elevate AI local voice pipeline](docs/assets/architecture-pipeline.png)

*Browser (mic + energy VAD) → FastAPI WebSocket → Faster-Whisper → Ollama (`SPEAK` / `FEEDBACK`) → Kokoro TTS. Long-term memory: SQLite on disk, queried only by the app.*

## Status

| Phase | Scope | Status |
|-------|--------|--------|
| 1 | Local STT → LLM → TTS inference | **Done** |
| 2 | WebSocket streaming + barge-in | **Done** |
| 3 | React UI + mic + energy VAD | **Done** (Studio Nocturne gold / night) |
| 4a | Dual channel `SPEAK` / `FEEDBACK` + Coach notes | **Done** |
| 4b | SQLite memory (`data/elevate.db`) | **Done** (brief + turn ingest) |
| 4c | Shadowing | Pending |

Warm batch ~**3.3s**. Streaming **TTFA ~2.1s**. Ollama cold load ~60–80s (lifespan warmup + `keep_alive=-1`).

Windows: no system CUDA Toolkit. The app bootstraps `torch/lib` DLLs. Pin **`onnxruntime-gpu==1.20.2`** (1.29+ needs CUDA 13).

## How a session works

1. Open [http://localhost:5173](http://localhost:5173) (backend must be on `:8000`, Ollama on `:11434`).
2. Pick a **scenario** in the left panel (Free Conversation, Job Interview, …). This is a binding instruction to the tutor, not a label.
3. **Start Session** and allow the microphone.
4. Speak. After **~1.5 s** of silence the turn is sent (or click *or send now*).
5. Hear the tutor. Grammar / phrasing stay in **Coach notes** — never spoken.
6. **Esc** or the stop square interrupts TTS. Moon / sun toggles Gold ↔ Night.

Learner profile in SQLite: **Angello · B2**.

## Repository layout

```
app/                 FastAPI backend (STT, LLM, TTS, WebSocket, SQLite)
frontend/            Vite + React + TypeScript UI
scripts/             Model download, GPU E2E latency probe
tests/               Unit tests (no GPU)
static/              Phase-2 HTML demo served at :8000/
docs/                PRD, architecture, design, backlog, context
docs/assets/         README diagram
design/              Moodboard + shader references
ElevateAI Desing/    Studio Nocturne HTML sources (gold / night / orbs)
data/                SQLite + samples (gitignored)
models/              ONNX weights (gitignored)
```

## Prerequisites

| Component | Notes |
|-----------|--------|
| Python **3.11 or 3.12** | 3.14 is not supported by torch / ctranslate2 |
| NVIDIA RTX 3060 12GB | CUDA 12.x driver |
| [Ollama](https://ollama.com/download) | `llama3.1:8b` pulled and **running** |
| Node.js 20+ | Frontend |

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip uninstall -y onnxruntime onnxruntime-gpu
pip install "onnxruntime-gpu==1.20.2"
copy .env.example .env
python scripts/download_models.py
ollama pull llama3.1:8b
cd frontend; npm install
```

## Run (two processes)

**Backend**

```powershell
.\.venv\Scripts\Activate.ps1
$env:Path = "$env:LOCALAPPDATA\Programs\Ollama;" + $env:Path
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend**

```powershell
cd frontend
npm run dev
```

| URL | Role |
|-----|------|
| http://localhost:5173 | **Product UI** (orb, VAD, Coach notes, themes) |
| http://127.0.0.1:8000/ | Phase-2 HTML demo only |
| `ws://…/ws/audio` | Voice pipeline (Vite proxies `/ws` → `:8000`) |

Ollama is a **separate** process (`http://127.0.0.1:11434`). FastAPI talks to it over HTTP; the UI never talks to Ollama directly.

## Dual channel, scenarios & memory

- The LLM emits `<<<SPEAK>>>` (TTS + transcript) and `<<<FEEDBACK>>>` (JSON → sidebar). TTS never sees JSON.
- **Scenario** is sent in `CONFIG` and injected as a binding block at the end of the system prompt. Switching scenario mid-session clears turn history so the tutor does not keep the previous topic.
- Session history (last ~6 turns) lives in RAM on the WebSocket.
- **SQLite** (`data/elevate.db`): FastAPI reads/writes only. Ollama never runs SQL — the app injects a short *memory brief* into the prompt. Details: [architecture §9](docs/architecture.md).

## UI (Studio Nocturne)

| Theme | Look |
|-------|------|
| **Gold** (default) | `#0E0C0A`, liquid amber orb (ANIMATION_12) |
| **Night** | `#0A0908`, cream-core orb (ANIMATION_17), same chrome / fonts / tick rings |

Sources: `ElevateAI Desing/`. Tokens: [docs/design-identity.md](docs/design-identity.md).

## VRAM budget (12 GB)

| Component | Approx. |
|-----------|---------|
| Faster-Whisper `medium.en` fp16 | 2–3 GB |
| Ollama 7–8B Q4/Q5 | 5.5–6.5 GB |
| Kokoro ONNX | ~0.5 GB |
| **Total** | **~8.5–10 GB** |

## Tests

```powershell
.\.venv\Scripts\python.exe tests\test_protocol.py
.\.venv\Scripts\python.exe tests\test_memory.py
python scripts/test_inference_pipeline.py   # GPU E2E latency
```

(`pytest` is optional; the `tests/` scripts also run as `__main__`.)

## Docs

| File | Content |
|------|---------|
| [README.es.md](README.es.md) | Guía operativa en español |
| [docs/architecture.md](docs/architecture.md) | Diseño de sistema + VRAM + SQLite |
| [docs/prd.md](docs/prd.md) | Requisitos de producto |
| [docs/design-identity.md](docs/design-identity.md) | Studio Nocturne (gold / night) |
| [docs/backlog.md](docs/backlog.md) | Siguiente trabajo |
| [docs/context.md](docs/context.md) | Log de decisiones |

## License

MIT — see [LICENSE](LICENSE).
