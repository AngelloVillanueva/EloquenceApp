# context.md — Memoria de conversación y decisiones

Documento vivo. Resume lo hablado y decidido sobre **Eloquence**.  
Última actualización: **2026-09-07** — Hub con orbe + Listen & Repeat con coaching.

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
| 4c | Shadowing | **Hecha** |

---

## 4. Cómo correr

```
Ollama  →  127.0.0.1:11434  (debe estar abierto)
Backend →  uvicorn app.main:app --host 127.0.0.1 --port 8000
Frontend →  cd frontend && npm run dev  →  http://localhost:5173
```

- `:5173` = app de producto. `:8000/` = demo HTML Fase 2.
- Vite proxy: `/ws` y `/api` → `:8000`.
- Flujo: **Hub** → escenario → Start Session → habla → 1.5 s silencio → tutor → Coach notes. End → recap → Hub o Start. **Listen & Repeat** (Kokoro + Whisper) desde Hub o un slip de pronunciación. Esc interrumpe.

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
- **X:** Session UX: chip de escenario en topbar, log acumulado de Coach notes, recap al End (sin score, PDF ni replay).
- **Y:** Hub (métricas SQLite + escenarios + Start Session) y Shadowing Listen & Repeat (`/api/tts`, `/api/shadow/*`).
- **Z:** El orbe vive también en Hub (reposo) y en Listen & Repeat (reacciona a Listen/Repeat). Escenarios = *session focus* (pills), no acciones. Escala tipográfica con mínimo 12 px. Shadow añade significado en español (`/api/shadow/gloss` vía Ollama), Prev/Next y **cómo corregir** la fonética (reglas para hispanohablantes en `app/services/shadow.py`).
- **AA:** CEFR real (B1/B2/C1). `spoken_tutor_prompt(level)` + `PATCH /api/memory/level`. Banco Listen & Repeat ~22 frases con `cefr`. Guardrail: se recorta español de SPEAK antes de TTS.

---

## 7. Decisiones congeladas

1. 100% local — sin cloud en el camino crítico.
2. VRAM: STT 2–3 + LLM 5.5–6.5 + TTS ~0.5 + headroom.
3. Canal dual: hablado → TTS; JSON → sidebar (nunca al TTS).
4. SQLite: solo FastAPI. El LLM nunca ejecuta SQL; recibe un *memory brief*.
5. Python 3.12; `onnxruntime-gpu==1.20.2`.
6. Nivel default **B2**. B1 y B2 reciben Coach notes (`note`/`tip`/`notes`) en español; `<<<SPEAK>>>` es siempre inglés (Kokoro no habla español). C1 recibe notes en inglés. Escenarios: `free`/`vocab` ≥ B1, `job` ≥ B2, `arch`/`nego` ≥ C1.
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

**Sistema de themes (2026-09-07).** Cinco temas en `data-theme`, elegidos desde `ThemePicker`
en la topbar y persistidos en `localStorage` (`eloquence-theme`; lee `elevate-theme` legacy una vez).

| Tema | Fondo | Acento | Forma de orbe |
|------|-------|--------|---------------|
| Studio Gold (default) | `#0E0C0A` | ámbar `#E8A87C` | liquid (ANIMATION_12) |
| Porcelain Night | `#08090C` frío | champán `#EBD9BC` | core (ANIMATION_17) |
| Ember | `#0C0706` | óxido `#E4693F` | liquid |
| Verdigris | `#06100E` | verdín `#6FD3B4` | core |
| Daylight | papel `#F7F2EA` | terracota `#B0642B` | liquid, blend `normal` |

Tokens en dos capas dentro de `globals.css`:

- **Capa 1 (paleta).** ~24 valores crudos por tema: fondos, textos, acento, `--on-accent`,
  `--border`, `--interrupt`, la paleta del orbe (`--orb-core`, `--orb-glow-1/2`, `--orb-form`)
  y el grano (`--grain-opacity`, `--grain-blend`).
- **Capa 2 (derivados + semánticos).** `--accent-glow/neon`, `--border-accent`, `--blur-glass`,
  `--scrim`, `--orb-shadow-*`, `--shadow-pop/panel`, vignette, y el eje semántico
  `--ok / --warn / --danger` (+ `-soft`), que ya **no** es el acento: "lo lograste" y "marca"
  dejaron de ser el mismo color.

El grano vive en la capa 1 porque cuánta textura tiene un fondo es parte de la identidad del
tema, y cada luminancia necesita distinta cantidad para leerse como película y no como ruido:
Gold `.26`, Porcelain Night `.18`, Ember `.30`, Verdigris `.22`, Daylight `.14` con `multiply`
(sobre papel el grano oscurece en vez de levantar, así que necesita mucho menos).
La capa 2 **no** puede declararlo o pisaría el valor de cada tema.

`:root` y `[data-theme='x']` empatan en especificidad, así que **cualquier override de la capa 2
va después del bloque `:root`**, no en la paleta del tema (ver Daylight). Ponerlo arriba lo pisa.

Los shaders del orbe reciben el color por uniform (`u_core`, `u_glow1`, `u_glow2`) y
`VoiceOrb` los lee de los tokens CSS con `theme/palette.ts`, así que un tema nuevo es solo un
bloque de tokens: nada de GLSL. `ThemeContext` escribe `data-theme` **antes** del re-render
(la fuente de verdad es el DOM, el state sólo lo espeja) porque el orbe y `ZenParticles`
muestrean `getComputedStyle`; con un efecto habrían leído el tema saliente.

El acento quedó reservado para lo accionable: los kickers de sección pasaron a `--text-subtle`
para que el CTA primario no compita con seis etiquetas ámbar por pantalla.

Fuentes de diseño: `ElevateAI Desing/` (gold standard, night standard, Orb 2, Obr Nightmode, mobile).

**Layout escritorio (2026-09-07).** Hub y Shadow usan `.studio-shell` + grid `hero | panel`
(2 columnas ≥1024 px, 1180 px máx, colapsa a una columna por debajo). El hero lleva orbe +
saludo + CTA; el panel lleva focus/progress/memoria (Hub) o corrección/cola (Shadow).
Los escenarios son una **lista**, no pills: envolvían 3+2 y se veía desordenado.
Atmósfera: grano `feTurbulence` **inline** (antes se descargaba de `transparenttextures.com`,
así que offline la app se veía plana), bloom ámbar y vignette en `.studio-shell::before/::after`,
`ZenParticles` ahora en las tres pantallas.
Tipografía: los tokens `--fs-*` suben un paso en `@media (min-width: 1280px)` — 16 px de body
es tamaño de teléfono en un monitor de 1440 px.

---

## 10. Archivos clave

```
app/                      FastAPI (STT, LLM, TTS, /ws/audio, memory)
app/prompts/tutor_system.py   B2 + scenario_instruction()
app/services/memory.py        SQLite
frontend/                 Vite + React (:5173)
frontend/src/orb/         shaders liquid / core (color por uniform)
frontend/src/theme/       ThemeContext (5 temas) + palette.ts (tokens → WebGL)
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
