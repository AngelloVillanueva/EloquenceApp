# context.md — Memoria de conversación y decisiones del proyecto

> Documento vivo de respaldo. Resume todo lo hablado y decidido en las sesiones de Cursor sobre **Elevate AI / Local AI English Voice Tutor (Codybot Architecture)**.  
> Última actualización: **2026-09-02** — Turno Q (docs + diseño SQLite).

---

## 1. Identidad del proyecto

| Campo | Valor |
|-------|-------|
| Nombre producto | Elevate AI |
| Arquitectura | Codybot-style, 100% local |
| Objetivo | Tutor de inglés por voz B1/B2 → C1, sin suscripción cloud |
| KPI latencia | ~1.5–2.0 s voz-a-voz (TTFA con streaming) |
| Hardware | NVIDIA GeForce RTX 3060 **12 GB** VRAM |
| Repo local | `c:\Users\Angello\Desktop\AI FDE\IdiomasApp\` |

---

## 2. Stack técnico (en uso)

| Capa | Tecnología | Detalle |
|------|-----------|---------|
| Runtime | Python 3.12 | `.venv` |
| Backend | FastAPI + uvicorn | `:8000` |
| Frontend | Vite + React + TS + Tailwind | `:5173` |
| WebSocket | `/ws/audio` | PCM + JSON events |
| STT | Faster-Whisper `medium.en` | CUDA float16 |
| LLM | Ollama `llama3.1:8b` | keep_alive=-1, num_ctx=2048, num_predict=220 |
| TTS | Kokoro ONNX GPU | Piper fallback |
| Dual channel | `<<<SPEAK>>>` / `<<<FEEDBACK>>>` | TTS limpio + Coach notes |
| VAD | Energía RMS cliente | ~750 ms silencio → END_TURN |
| Memoria sesión | lista en WS handler | últimos 6 turnos (12 msgs) |
| Memoria larga | **SQLite (diseñado, no implementado)** | `data/elevate.db` |

---

## 3. Estado de fases

| Fase | Contenido | Estado |
|------|-----------|--------|
| 1 | Inferencia local STT/LLM/TTS | **Hecha** |
| 2 | WS streaming + barge-in + TTFA | **Hecha** |
| 3 | Frontend voz (mic, orb, VAD, UI) | **MVP hecho** (UI estética pendiente) |
| 4a | Canal dual + Coach notes | **Hecho** |
| 4b | SQLite memoria entre sesiones | **Diseñado** (siguiente implementación) |
| 4c | Shadowing | Pendiente |

---

## 4. Cómo correr (dos procesos)

```
Terminal A — backend
  uvicorn app.main:app --host 127.0.0.1 --port 8000

Terminal B — frontend
  cd frontend && npm run dev
  → http://localhost:5173
```

- `:8000/` = demo HTML Fase 2 (`ws_demo.html`) — no es la app React.
- `:5173` = UI real (orbe, Coach notes, VAD).
- Vite proxy: `/ws` → `:8000`.

---

## 5. Protocolo WS (resumen)

**Cliente → servidor:** PCM16 binary, `END_TURN`, `CANCEL_AUDIO`, `CONFIG`, `PING`  
**Servidor → cliente:** `READY`/`STATE`, `TRANSCRIPT`, `TOKEN`, `SENTENCE`, `FEEDBACK`, `AUDIO_META`, PCM TTS, `TURN_DONE`, `CANCELLED`, `ERROR`

---

## 6. Cronología (turnos clave)

- **A–H:** Fase 1–2, bugs Ollama/JS/caché, estabilidad GPU executor + barge-in.
- **I–L:** Identidad Booth; Hub vs Session; rediseño aesthetic.
- **M–N:** Scaffold React; mic + TTS playback.
- **O:** Prompt tutor hablado + VAD automático.
- **P:** Canal dual SPEAK/FEEDBACK + panel Coach notes.
- **Q:** Docs + diseño SQLite en `docs/architecture.md` §9.
- **R:** Reorganización de carpetas estilo FDE (docs/, tests/, diagrama en README) para GitHub.

---

## 7. Decisiones congeladas

1. 100% local — sin cloud en el camino crítico.
2. VRAM: STT 2–3 + LLM 5.5–6.5 + TTS ~0.5 + headroom.
3. Canal dual: hablado → TTS; JSON → sidebar (nunca al TTS).
4. **SQLite lo escribe/lee solo FastAPI** — el LLM **nunca** ejecuta SQL; recibe un *memory brief* en texto.
5. Python 3.12; `onnxruntime-gpu==1.20.2`.

---

## 8. SQLite — idea acordada (ver `docs/architecture.md` §9)

| Pregunta | Respuesta |
|----------|-----------|
| ¿Dónde vive? | Archivo local `data/elevate.db` en el PC del usuario |
| ¿Quién consulta? | **La app (FastAPI)**, no Ollama |
| ¿Cómo “recuerda” el LLM? | Al iniciar sesión / cada N turnos, la app lee SQLite y mete un brief corto en el prompt |
| ¿Qué ve el Hub? | REST `/api/memory/*` → streaks, errores, vocab — sin LLM |
| ¿Qué se guarda tras un turno? | Feedback JSON → tablas `errors`, `vocab`, `sessions` |

---

## 9. Archivos clave

```
app/                      FastAPI (STT, LLM, TTS, /ws/audio)
frontend/                 Vite + React (:5173)
tests/                    unit tests (sin GPU)
scripts/                  download + probe E2E GPU
docs/architecture.md      sistema + §9 SQLite
docs/prd.md               PRD
docs/assets/              diagrama del README
design/moodboard/         identidad visual
static/ws_demo.html       demo Fase 2 (:8000/)
```

---

*Mantener actualizado al cerrar cada fase o decisión relevante.*
