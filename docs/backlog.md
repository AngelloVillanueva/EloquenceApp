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
- [x] Shadowing “Escucha y Repite” (Hub + Listen & Repeat + practice desde pronunciación).

## Producto / UI

- [x] Session chip (escenario visible), log de Coach notes por turno, recap al End (sin score).
- [x] **Hub**: orbe en reposo, focus pills, CTA Start Session + Listen & Repeat, last session, slips/vocab.
- [x] Escala tipográfica (`--fs-*`, mínimo 12 px) aplicada en Hub / Shadow / Coach notes.
- [x] **Layout escritorio**: Hub y Shadow en grid hero + panel (2 col ≥1024 px), focus como lista en vez de pills que envuelven 3+2, step-up tipográfico ≥1280 px, grano SVG local + bloom/vignette (`.studio-shell`).
- [x] **LevelSelector B1·B2·C1**: persistido en SQLite, cableado al system prompt. B1/B2: Coach notes en español; SPEAK siempre inglés. Escenarios filtrados por `minLevel`. Banco Listen & Repeat por CEFR.
- [ ] Tipografía brand definitiva (Syne / Outfit / Geist).
- [x] **Themes tipo VS Code**: 5 paletas (Gold, Porcelain Night, Ember, Verdigris, Daylight) + `ThemePicker`, tokens en 2 capas, orbe recoloreado por uniforms, semánticos `--ok/--warn/--danger`.
