# context.md — Memoria de conversación y decisiones

Documento vivo. Resume lo hablado y decidido sobre **Eloquence**.  
Última actualización: **2026-09-04** — rebrand Eloquence; eval Gemma vs Llama.

---

## 1. Identidad

| Campo | Valor |
|-------|-------|
| Producto | Eloquence |
| SQLite | `data/elevate.db` (path histórico; no se migra en el rebrand) |
| GitHub remoto | `ElevateAIApp` (sin renombrar en este paso) |
| Arquitectura | 100% local (STT + LLM + TTS en una GPU) |
| Alumno | Hispanohablante **B2** (perfil SQLite: Angello) rumbo a C1 |
| KPI | TTFA ~1.5–2.0 s (streaming) |
| Hardware | NVIDIA RTX 3060 **12 GB** |
| Repo | `c:\Users\Angello\Desktop\AI FDE\IdiomasApp\` |

---

## 2. Stack en uso

| Capa | Tecnología | Detalle |
|------|-----------|---------|
| Runtime | Python 3.12 | `.venv` |
| Backend | FastAPI + uvicorn | `:8000` |
| Frontend | Vite + React + TS + Tailwind | `:5173` |
| WebSocket | `/ws/audio` | PCM + JSON (`CONFIG`, `END_TURN`, `CANCEL_AUDIO`) |
| STT | Faster-Whisper `medium.en` | CUDA float16 |
| LLM | Ollama `llama3.1:8b` | keep_alive=-1, num_ctx=2048, num_predict=120 (`.env`) |
| TTS | Kokoro ONNX GPU | Piper fallback |
| Dual channel | `<<<SPEAK>>>` / `<<<FEEDBACK>>>` | TTS limpio + Coach notes |
| VAD | Energía RMS en cliente | **1500 ms** de silencio → `END_TURN` |
| Escenario | `CONFIG.scenario` | Bloque `[SCENARIO]` al final del prompt |
| Memoria sesión | lista en el handler WS | últimos 6 turnos (12 msgs) |
| Memoria larga | SQLite **implementada** | `data/elevate.db` · solo FastAPI |

---

## 3. Fases

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Inferencia local STT/LLM/TTS | **Hecha** |
| 2 | WS streaming + barge-in + TTFA | **Hecha** |
| 3 | Frontend voz + Studio Nocturne | **Hecha** |
| 4a | Canal dual + Coach notes | **Hecha** |
| 4b | SQLite (brief + ingest de turnos) | **Hecha** |
| 4c | Shadowing | Pendiente |

---

## 4. Cómo correr

```
Ollama  →  127.0.0.1:11434  (debe estar abierto)
Backend →  uvicorn app.main:app --host 127.0.0.1 --port 8000
Frontend →  cd frontend && npm run dev  →  http://localhost:5173
```

- `:5173` = app de producto. `:8000/` = demo HTML Fase 2.
- Vite proxy: `/ws` y `/api` → `:8000`.
- Flujo: escenario → Start Session → habla → 1.5 s silencio → tutor → Coach notes. Esc interrumpe.

---

## 5. Protocolo WS

**Cliente → servidor:** PCM16 binary, `END_TURN`, `CANCEL_AUDIO`, `CONFIG`, `PING`  
**Servidor → cliente:** `READY`/`STATE`, `TRANSCRIPT`, `TOKEN`, `SENTENCE`, `FEEDBACK`, `AUDIO_META`, PCM TTS, `TURN_DONE`, `CANCELLED`, `ERROR`

`CONFIG.scenario` se aplica siempre. Si cambia el escenario en la misma conexión, se vacía `history`.

---

## 6. Cronología

- **A–H:** Fase 1–2, bugs Ollama/JS/caché, GPU executor + barge-in.
- **I–L:** Identidad Booth; Hub vs Session.
- **M–P:** React, mic, TTS, VAD, canal dual, Coach notes.
- **Q–R:** Docs + repo estilo FDE; GitHub.
- **S:** Orbe WebGL + carpeta `ElevateAI Desing/` (gold / night / orbs).
- **T:** Nivel **B2**; VAD **750 → 1500 ms**.
- **U:** Night = mismo chrome que Gold (anillos, Plus Jakarta, orbe más grande); escenarios **vinculantes**.
- **V:** README, arquitectura y este context alineados con el código.
- **W:** Rebrand a **Eloquence** (wordmark de una palabra, sin sufijo AI). SQLite sigue en `data/elevate.db`. Eval Gemma vs Llama en Ollama (ver §11).

---

## 7. Decisiones congeladas

1. 100% local — sin cloud en el camino crítico.
2. VRAM: STT 2–3 + LLM 5.5–6.5 + TTS ~0.5 + headroom.
3. Canal dual: hablado → TTS; JSON → sidebar (nunca al TTS).
4. SQLite: solo FastAPI. El LLM nunca ejecuta SQL; recibe un *memory brief*.
5. Python 3.12; `onnxruntime-gpu==1.20.2`.
6. Nivel de producto actual: **B2** (no tratar al alumno como C1).
7. Fin de turno: **1.5 s** de silencio (dudas y frases incompletas).
8. UI: Studio Nocturne. Night reutiliza el formato Gold; solo cambian fondo + shader del orbe.
9. El escenario no es cosmética: instruye al tutor y, al cambiar, resetea el hilo.
10. Marca **Eloquence** (una palabra, sin sufijo AI). No se renombra `data/elevate.db` ni la carpeta `ElevateAI Desing/`.
11. LLM default: **Llama 3.1 8B** en Ollama. Gemma 2 9B es opcional (`OLLAMA_MODEL=gemma2:9b`); ver §11.

---

## 8. SQLite (hecho — ver `docs/architecture.md` §9)

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde? | `data/elevate.db` |
| ¿Quién consulta? | FastAPI `MemoryService` |
| ¿Cómo recuerda el LLM? | Brief de texto al abrir / al `CONFIG` |
| REST | `GET /api/memory` |
| Tras un turno | `turns` + upsert `errors` / `vocab` |

---

## 9. UI (Studio Nocturne)

| Tema | Orbe | Fondo |
|------|------|--------|
| Gold (default) | ANIMATION_12 líquido ámbar | `#0E0C0A` |
| Night | ANIMATION_17 núcleo crema + anillos | `#0A0908` |

Misma topbar, mismas fuentes (Plus Jakarta + JetBrains Mono), mismos ticks alrededor del orbe. Toggle luna/sol en `localStorage` (`eloquence-theme`; still reads legacy `elevate-theme` once).

Fuentes de diseño: `ElevateAI Desing/` (gold standard, night standard, Orb 2, Obr Nightmode, mobile).

---

## 10. Archivos clave

```
app/                      FastAPI (STT, LLM, TTS, /ws/audio, memory)
app/prompts/tutor_system.py   B2 + scenario_instruction()
app/services/memory.py        SQLite
frontend/                 Vite + React (:5173)
frontend/src/orb/         shaders gold / night
tests/                    protocol + memory (sin GPU)
docs/architecture.md      sistema + §6.3 escenarios + §9 SQLite
docs/design-identity.md   tokens Studio Nocturne
ElevateAI Desing/         HTML de referencia visual
```

---

## 11. Eval Gemma 2 9B vs Llama 3.1 8B (2026-09-04)

Ollama ya era el servidor; se evaluó **otro modelo** en el mismo `:11434`, no un runtime nuevo.

| | `llama3.1:8b` (sigue default) | `gemma2:9b` (opcional) |
|--|------------------------------|-------------------------|
| VRAM warm (`nvidia-smi` tarjeta) | 5354 MB | 6554 MB |
| Primer SPEAK warm (turnos 2–5) | 0.43 s | 0.65 s |
| Dual `SPEAK`+JSON válido | 1/5 (JSON recortado por `num_predict=120`) | 5/5 |
| JSON filtrado al TTS (tras fix holdback) | 0/5 | 0/5 |

Harness: `scripts/eval_ollama_models.py`. Conclusión: **no cambiar el default**. Gemma cabe en 12 GB con STT+TTS pero deja menos holgura; Llama es más rápido al primer token. Override: `OLLAMA_MODEL=gemma2:9b` en `.env`.

Durante la eval se corrigió `_holdback_for_marker` en `app/ws/dual_channel.py` (el token `<<<` se filtraba al canal hablado).

---

*Actualizar al cerrar cada fase o decisión que cambie el comportamiento.*
