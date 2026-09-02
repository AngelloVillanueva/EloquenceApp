# Elevate AI

**100% local English voice tutor** — STT → LLM → TTS on a single NVIDIA RTX 3060 12GB. No cloud APIs on the critical path, no subscription.

Designed for Spanish speakers moving from **B1/B2 → C1** professional fluency.

![Elevate AI local voice pipeline](docs/assets/architecture-pipeline.png)

*Browser (mic + VAD) → FastAPI WebSocket → Faster-Whisper → Ollama (SPEAK / FEEDBACK) → Kokoro TTS. Long-term memory: SQLite on disk, queried only by the app.*

## Status

| Phase | Scope | Status |
|-------|--------|--------|
| 1 | Local STT → LLM → TTS inference | **Done** |
| 2 | WebSocket streaming + barge-in | **Done** |
| 3 | React UI + mic + energy VAD | **MVP** |
| 4a | Dual channel `SPEAK` / `FEEDBACK` + Coach notes | **Done** |
| 4b | SQLite long-term memory | **Designed** ([docs/architecture.md](docs/architecture.md) §9) |
| 4c | Shadowing | Pending |

Warm batch ~**3.3s**. Streaming **TTFA ~2.1s**. Ollama cold load ~60–80s (lifespan warmup + `keep_alive=-1`).

Windows: no system CUDA Toolkit. The app bootstraps `torch/lib` DLLs. Pin **`onnxruntime-gpu==1.20.2`** (1.29+ needs CUDA 13).

## Repository layout

```
app/                 FastAPI backend (STT, LLM, TTS, WebSocket)
frontend/            Vite + React + TypeScript UI
scripts/             Model download, GPU E2E latency probe, setup
tests/               Unit tests (no GPU)
static/              Phase-2 HTML demo served at :8000/
docs/                PRD, architecture, design, backlog
docs/assets/         README diagram
design/moodboard/    Visual identity references
data/                Runtime samples / SQLite (local, gitignored)
models/              ONNX weights (gitignored — download via script)
```

## Prerequisites

| Component | Notes |
|-----------|--------|
| Python **3.11 or 3.12** | 3.14 is not supported by torch / ctranslate2 |
| NVIDIA RTX 3060 12GB | CUDA 12.x driver |
| [Ollama](https://ollama.com/download) | `llama3.1:8b` pulled and running |
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
| http://localhost:5173 | **Product UI** (orb, VAD, Coach notes) |
| http://127.0.0.1:8000/ | Phase-2 HTML demo only |
| `ws://…/ws/audio` | Voice pipeline (Vite proxies `/ws` → `:8000`) |

**Flow:** Start Session → speak → ~0.75s silence sends the turn → hear the tutor → **Coach notes** for grammar / C1 phrasing. Esc interrupts TTS.

## Dual channel & memory

- The LLM emits `<<<SPEAK>>>` (TTS + transcript) and `<<<FEEDBACK>>>` (JSON → sidebar). TTS never sees JSON.
- Session history (last ~6 turns) lives in RAM on the WebSocket.
- **SQLite** (`data/elevate.db`, planned): FastAPI reads/writes only. Ollama never runs SQL — the app injects a short *memory brief* into the prompt. Details: [architecture §9](docs/architecture.md).

## VRAM budget (12 GB)

| Component | Approx. |
|-----------|---------|
| Faster-Whisper `medium.en` fp16 | 2–3 GB |
| Ollama 7–8B Q4/Q5 | 5.5–6.5 GB |
| Kokoro ONNX | ~0.5 GB |
| **Total** | **~8.5–10 GB** |

## Tests

```powershell
python -m pytest tests/                 # no GPU
python scripts/test_inference_pipeline.py   # GPU E2E latency
```

## Docs

| File | Content |
|------|---------|
| [README.es.md](README.es.md) | Spanish ops guide |
| [docs/architecture.md](docs/architecture.md) | System design + SQLite |
| [docs/prd.md](docs/prd.md) | Product requirements |
| [docs/design-identity.md](docs/design-identity.md) | Booth visual identity |
| [docs/backlog.md](docs/backlog.md) | Next work |
| [docs/context.md](docs/context.md) | Decision log |

## License

MIT — see [LICENSE](LICENSE).
