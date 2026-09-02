# Identidad visual — Elevate AI

> **Estética base:** Booth (oscuro cálido + ámbar). Atlas y Signal descartadas como look.  
> **Turno L (activo):** Rediseño consciente Hub + Session; level selector eliminado de pantalla de sesión.

Actualizado: 2026-09-02

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
/* Base */
--bg:            #0E0C0A;
--bg-elevated:   #151210;
--surface:       #1C1916;
--surface-high:  #242018;

/* Texto */
--text:          #F2EDE5;
--text-muted:    #9C9288;
--text-subtle:   #5A5450;

/* Acento ámbar */
--accent:        #D4A574;
--accent-warm:   #C4925E;
--accent-glow:   rgba(212, 165, 116, 0.15);

/* Interrupt */
--interrupt:     #B85A48;
--interrupt-dim: rgba(184, 90, 72, 0.6);

/* Orbe */
--orb-idle:      #2A2520;
--orb-listen:    #3D352B;
--orb-speak:     #EDE6DC;

/* UI */
--border:        rgba(242, 237, 229, 0.07);
--border-amber:  rgba(212, 165, 116, 0.20);
--blur-surface:  rgba(14, 12, 10, 0.75);

/* Tipografía */
--font-brand:    'Syne', 'Geist', system-ui;
--font-ui:       'Inter', 'Source Sans 3', system-ui;
```

### Night variant
```css
/* Night mode = mismo layout, superficie más opaca, ámbar más vivo */
--bg:            #0A0908;
--surface:       #161311;
--accent:        #E0B080;          /* ámbar +10% saturation */
--text:          #F5F0E8;
--text-muted:    #A09688;
```

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
| Brand mark "Elevate" | Syne | 20px | 700 |
| "AI" (tag suave) | Syne | 14px | 400, ámbar |
| Heading Hub | Syne | 28px | 600 |
| Subtítulo / labels | Inter | 13px | 400–500 |
| Transcript | Inter | 14px | 400 |
| Métricas | Inter Mono | 11px | 500 |

**No usar:** fuentes serif, condensadas, o cualquier cosa que evoque "universidad" o "banco".

---

## 5. Pantalla: Hub (Dashboard)

### Propósito
Seleccionar escenario antes de entrar en sesión. Punto de partida natural.

### Layout

```
┌─ Elevate [A]I ─────────────────── [•] streak  [⚙] ─┐
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
┌─ Elevate AI ──────── [◉ 01:42] ── [TTFA 1.7s] ── [■] ─┐
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
│  │ Elevate "Absolutely. What I mean is that…"     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**El nivel de inglés no aparece en esta pantalla.** Se hereda del escenario elegido en Hub.

### Componentes y reglas

| Componente | Posición | Notas |
|------------|----------|-------|
| `BrandMark` | Top left | "Elevate AI" — pequeño, 18px |
| `SessionTimer` | Top center | `◉ MM:SS` — dot pulsa en speaking |
| `TtfaBadge` | Top right -2 | `TTFA 1.7s` mono, ámbar |
| `InterruptButton` | Top right | Ícono square-stop, coral `--interrupt`, 32×32px |
| `VoiceOrb` | Center | Estados: idle / listen / think / speak |
| `StateLabel` | Bajo orbe | "Listening…" / "Thinking…" / "Speaking…" — muted |
| `LiveTranscriptBox` | Bottom | Glassmorphism, 2 filas You/Elevate, auto-scroll |

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
