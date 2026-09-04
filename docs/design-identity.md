# Identidad visual — Eloquence

> **Estética base:** Studio Nocturne (Booth). Fuente de verdad: `ElevateAI Desing/`.  
> **Gold** = `gold standard` + orbe ANIMATION_12. **Night** = `night standard` + orbe ANIMATION_17.

Actualizado: 2026-09-04 — wordmark Eloquence

---

## 1. Arquitectura de pantallas

| Pantalla | Rol | Prioridad |
|----------|-----|-----------|
| **Hub** | Elegir escenario, ver progreso, arrancar sesión | Fase 3.5 |
| **Sesión Activa** | Voz: orbe + transcript + TTFA + interrupt | **Fase 3 ahora** |
| **Settings / Onboarding** | Nivel de inglés, voz, modelo LLM, GPU info | Post MVP |

---

## 2. Tokens de diseño (Booth)

```css
/* Gold studio — ElevateAI Desing/gold standard */
--bg:            #0E0C0A;
--surface:       #1A1714;
--text:          #E8E1DD;
--accent:        #E8A87C;          /* primary-container */
--interrupt:     #690002;
--border:        #2A241F;
--font-brand:    'Plus Jakarta Sans';
--font-ui:       'Plus Jakarta Sans';
--font-display:  'Noto Serif';
--font-mono:     'JetBrains Mono';
```

Toggle en topbar (`data-theme="gold" | "night"`). Persistido en `localStorage`.

### Night variant — `ElevateAI Desing/night standard`
```css
--bg:            #0A0908;
--surface:       #161311;
--accent:        #E0B080;
--interrupt:     #E85D4E;
--text:          #F5F0EB;
--font-ui:       'Noto Serif';     /* cuerpo editorial */
```

### Orbes
| Tema | Shader | Origen |
|------|--------|--------|
| Gold | ANIMATION_12 líquido ámbar | `ElevateAI Desing/Orb 2` |
| Night | ANIMATION_17 núcleo crema + anillos | `ElevateAI Desing/Obr Nightmode` |

---

## 3. Convenciones de layout

- **Grilla:** 12 col, padding horizontal 24px (mobile) / 40px (desktop 1280+).
- **Radios:** `--radius-sm: 6px` / `--radius-md: 12px` / `--radius-lg: 20px` / `--radius-full: 9999px`.
- **Elevación:** solo sombras suaves + borde semitransparente (no box-shadow grosero).
- **Glassmorphism:** `backdrop-filter: blur(20px)` + `background: var(--blur-surface)` para transcript.
- **Orbe:** SVG/Canvas animado, no imagen estática.

---

## 4. Tipografía

| Uso | Familia | Tamaño | Peso |
|-----|---------|--------|------|
| Brand mark Eloquence | Plus Jakarta Sans | 22px | 600 |
| Status gold | Plus Jakarta Sans | 16px | 400 |
| Status night | Noto Serif | 18px | 400 |
| Transcript | Plus Jakarta / Noto Serif (night) | 16px | 400 |
| Chips YOU / ELOQUENCE | JetBrains Mono | 10px | 500, caps |
| Telemetría / TTFA | JetBrains Mono | 11px | 400 |

**No usar:** fuentes serif, condensadas, o cualquier cosa que evoque "universidad" o "banco".

---

## 5. Pantalla: Hub (Dashboard)

### Propósito
Seleccionar escenario antes de entrar en sesión. Punto de partida natural.

### Layout

```
┌─ Eloquence ────────────────────── [•] streak  [⚙] ─┐
│                                                      │
│  Good evening, Angello.                              │
│  Level: C1  ·  Sessions this week: 3                │
│                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ 💼 Job       │ │ 🏛 Defense  │ │ 🤝 Nego...  │  │
│  │ Interview    │ │ Architecture│ │ tiation     │  │
│  │              │ │             │ │             │  │
│  │ C1 focus     │ │ Technical   │ │ Business    │  │
│  └──────────────┘ └──────────────┘ └─────────────┘  │
│                                                      │
│  ┌──────────────┐ ┌──────────────┐                  │
│  │ 💬 Free      │ │ 📚 Vocab    │                  │
│  │ Conversation │ │ Deep Dive   │                  │
│  └──────────────┘ └──────────────┘                  │
│                                                      │
│  Last session: 14 min  ·  TTFA avg 1.8s             │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │        ▶  Start Session                       │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Reglas de diseño Hub
- Tarjetas de escenario: 3 col desktop, scroll horizontal mobile.
- Seleccionar tarjeta = borde ámbar + check icon; no navega aún.
- Botón "Start Session" al fondo: ancho completo, color `--accent`, texto oscuro.
- Nivel de inglés NO tiene botones en esta pantalla: se muestra como dato (`Level: C1`) y se edita desde Settings.
- Sin sidebar: navegación es solo Settings (esquina) + tarjetas.

---

## 6. Pantalla: Sesión Activa (Focus / Zen)

### Layout

```
┌─ Eloquence ───────── [◉ 01:42] ── [TTFA 1.7s] ── [■] ─┐
│                                                         │
│                                                         │
│                    ╭───────────╮                        │
│                   ╱             ╲                       │
│                  │     ORBE      │                      │
│                   ╲             ╱                       │
│                    ╰───────────╯                        │
│                   ·  Listening…  ·                      │
│                                                         │
│                                                         │
│  ┌─ transcript ────────────────────────────────────┐    │
│  │ You    "Could you elaborate on that point—"     │    │
│  │ Eloquence "Absolutely. What I mean is that…"   │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**El nivel de inglés no aparece en esta pantalla.** Se hereda del escenario elegido en Hub.

### Componentes y reglas

| Componente | Posición | Notas |
|------------|----------|-------|
| `BrandMark` | Top left | "Eloquence" — Plus Jakarta 22px |
| `SessionTimer` | Top center | `◉ MM:SS` — dot pulsa en speaking |
| `TtfaBadge` | Top right -2 | `TTFA 1.7s` mono, ámbar |
| `InterruptButton` | Top right | Ícono square-stop, coral `--interrupt`, 32×32px |
| `VoiceOrb` | Center | Estados: idle / listen / think / speak |
| `StateLabel` | Bajo orbe | "Listening…" / "Thinking…" / "Speaking…" — muted |
| `LiveTranscriptBox` | Bottom | Glassmorphism, 2 filas You/Eloquence, auto-scroll |

### Interrupt button
- Tamaño máximo: 32×32 px, icono `■` (stop) o `⏸`.
- Color: `--interrupt-dim` en idle; `--interrupt` al hover/active.
- **No** texto largo "Interrupt". Un ícono es suficiente.
- Tooltip accesible: "Interrupt (Esc)".

### Orbe (estados)
| Estado | Apariencia |
|--------|-----------|
| `idle` | Oscuro, pulso lento, sin glow |
| `listening` | Expand leve, borde ámbar fino, react amplitude |
| `thinking` | Rotación suave, ámbar interno |
| `speaking` | Glow blanco/ámbar, bloom suave, react waveform |

---

## 7. Night mode

**Problema:** `#070605` + tokens oscuros = legibilidad cero, parece apagada.  
**Corrección:** subir superficies un step, mantener feeling nocturno sin sacrificar contraste.

```css
/* Night overrides */
--bg:            #0A0908;    /* was #070605 — 2 steps más claro */
--surface:       #161311;
--surface-high:  #1E1A16;
--text:          #F5F0E8;
--text-muted:    #A09688;    /* era #8F877C — más visible */
--accent:        #E0B080;    /* ámbar más saturado */
--border:        rgba(245, 240, 232, 0.09);
```

**Regla general:** ratio de contraste mínimo 4.5:1 para texto normal, 3:1 para texto grande/iconos.

---

## 8. Componentes descartados de sesión activa

| Elemento | Decisión |
|----------|---------|
| Botones C1 / C2 / Pro en sesión | **Eliminados** — van en Settings/onboarding |
| Eslogan bajo logo | Eliminado |
| Nivel como tag en sesión | Máximo un badge sutil, no botones clickeables |

---

## 9. Moodboard (archivos)

Carpeta: `design/moodboard/`

| Archivo | Descripción |
|---------|------------|
| `elevate-identity-booth-a1.png` | Primera iteración Booth |
| `elevate-identity-booth-refined.png` | Session gold standard anterior |
| `elevate-hub-v1.png` | Hub — Turno L |
| `elevate-session-v2.png` | Session Active — Turno L |
| `elevate-session-night-v2.png` | Session Night — Turno L |
| `elevate-architecture-diagram.png` | Diagrama de pipeline (copia en `docs/assets/`) |
