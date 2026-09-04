# Backlog — Eloquence

Ideas y deudas técnicas para más adelante (no bloquean Fase 3 UI).

## Rendimiento / GPU (desde feedback Signal)

- [ ] **Mostrar uso de VRAM/GPU en la UI** (o panel de estado): cuánto consume Whisper vs Ollama vs Kokoro en listening / thinking / speaking.
- [ ] Investigar **cómo medir** en Windows + RTX 3060 (p.ej. `nvidia-smi` vía proceso local, NVML, o endpoint `/api/gpu` en FastAPI).
- [ ] Evaluar **optimizaciones** según datos reales: cuantización LLM, unload selectivo, serializar mejor STT/TTS, bajar `num_ctx`, etc.
- [ ] Decidir si el indicador es continuo (sparklines) o solo “headroom OK / warning”.

## UX voz

- [x] AudioWorklet captura PCM (frontend).
- [x] VAD energía cliente → `END_TURN` automático (~1500 ms silencio). Silero WASM = mejora futura.
- [ ] Cue sutil al detectar fin de habla.
- [x] Atajos: Space/Esc = Interrupt.
- [ ] Atajo M = mute.

## Pedagogía (Fase 4)

- [x] Canal dual SPEAK / FEEDBACK → TTS limpio + sidebar Coach notes.
- [x] Memoria de errores / vocabulario C1 entre sesiones (SQLite `data/elevate.db` + `/api/memory`).
- [ ] Shadowing “Escucha y Repite”.

## Producto / UI

- [ ] Tipografía brand definitiva (Syne / Outfit / Geist).
- [ ] **Hub / Dashboard**: escenarios C1, métricas diarias, progreso, CTA “Start Call” (después del MVP Session Active).
- [ ] LevelSelector C1·C2·Pro cableado a system prompt / opciones Ollama.
- [ ] Tema night toggle (tokens Booth night).
