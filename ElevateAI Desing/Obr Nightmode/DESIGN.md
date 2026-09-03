---
name: Studio Nocturne
colors:
  surface: '#151311'
  surface-dim: '#151311'
  surface-bright: '#3c3936'
  surface-container-lowest: '#100e0c'
  surface-container-low: '#1d1b19'
  surface-container: '#221f1d'
  surface-container-high: '#2c2927'
  surface-container-highest: '#373432'
  on-surface: '#e8e1dd'
  on-surface-variant: '#d6c3b8'
  inverse-surface: '#e8e1dd'
  inverse-on-surface: '#33302d'
  outline: '#9e8d83'
  outline-variant: '#51443c'
  surface-tint: '#fbb88b'
  primary: '#ffc69f'
  on-primary: '#4e2604'
  primary-container: '#e8a87c'
  on-primary-container: '#693c19'
  inverse-primary: '#85532e'
  secondary: '#ffb4a9'
  on-secondary: '#690002'
  secondary-container: '#8b1913'
  on-secondary-container: '#ff9a8c'
  tertiary: '#d4d1cb'
  on-tertiary: '#31312c'
  tertiary-container: '#b8b6b0'
  on-tertiary-container: '#484743'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdcc6'
  primary-fixed-dim: '#fbb88b'
  on-primary-fixed: '#301400'
  on-primary-fixed-variant: '#693c19'
  secondary-fixed: '#ffdad5'
  secondary-fixed-dim: '#ffb4a9'
  on-secondary-fixed: '#410001'
  on-secondary-fixed-variant: '#8b1913'
  tertiary-fixed: '#e5e2db'
  tertiary-fixed-dim: '#c9c6c0'
  on-tertiary-fixed: '#1c1c18'
  on-tertiary-fixed-variant: '#474742'
  background: '#151311'
  on-background: '#e8e1dd'
  surface-variant: '#373432'
typography:
  display-lg:
    fontFamily: Noto Serif
    fontSize: 48px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-md-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.1em
  telemetry:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
---

## Brand & Style
The design system is built around a "Dark Studio" aesthetic, mimicking the focused, high-fidelity environment of a professional sound stage. It targets learners who value deep focus, premium quality, and sophisticated technology.

The visual style is a hybrid of **Minimalism** and **Glassmorphism**. It uses heavy whitespace (negative space), high-quality typography, and translucent layered surfaces to create a sense of depth without clutter. The emotional response should be one of calm, rhythmic focus—positioning the AI not as a robotic tool, but as a refined, human-centric mentor. All UI elements should feel like physical hardware controls found in a high-end recording studio: precise, responsive, and tactile.

## Colors
The palette is rooted in a warm, "Charcoal" foundation to reduce eye strain during long study sessions. 

- **Primary (Amber/Gold):** Reserved for "active" energy—voice orbs, speaker labels, and primary action highlights. It represents the "spark" of intelligence.
- **Secondary (Coral Red):** Used exclusively for destructive or high-priority interruptions, such as the "Stop" or "Interrupt" button.
- **Neutral (Warm Off-White/Muted Gray):** Used for typography to maintain a soft contrast that feels high-end and legible against the dark background.
- **Surface (Glass):** A semi-transparent dark tint that creates the signature studio layering effect.

## Typography
The typographic scale emphasizes a hierarchy between "Brand/Editorial" and "Interface/Utility."

- **Serif (Noto Serif):** Used sparingly for brand marks and major section headers to evoke a sense of tradition and academic excellence.
- **Sans (Plus Jakarta Sans):** The primary workhorse for the UI. Its soft, modern curves balance the technical nature of the AI.
- **Monospace (JetBrains Mono):** Used for technical telemetry (bitrate, latency, voice status) and labels. It should always be uppercase when used as a label to reinforce the "instrument cluster" aesthetic.

## Layout & Spacing
This design system utilizes a **Fluid Grid** model with generous internal padding to maintain the minimalist feel.

- **Desktop:** 12-column grid with a 1200px max-width container. Gutters are fixed at 24px to ensure breathing room between glass modules.
- **Mobile:** 4-column grid with 16px side margins.
- **Rhythm:** All spacing is based on a 4px baseline grid. Use `md (16px)` for standard component spacing and `xl (40px)` for vertical section breathing room.
- **Alignment:** Content should generally be center-aligned in "Focus Modes" (during active conversation) and left-aligned in "Dashboard Modes" (lesson browsing).

## Elevation & Depth
Depth is communicated through **Glassmorphism** and subtle **Tonal Layering** rather than traditional drop shadows.

- **Layer 0 (Background):** Solid #12100E.
- **Layer 1 (Cards/Panels):** #1A1714 at 60% opacity with a 16px background blur. This creates a "frosted" look where the background glows slightly through the UI.
- **Layer 2 (Floating Elements):** Popovers or tooltips use a higher opacity (80%) and a subtle 1px inner glow (top-down) using #F5F2EB at 10% opacity.
- **Outlines:** Every glass surface must have a 1px solid border (#2A241F) to define its edges against the dark background.

## Shapes
The shape language is "Soft-Modern." 

- **Cards & Modules:** Use `rounded-lg` (16px) to match the glassmorphic aesthetic.
- **Interactive Elements:** Buttons and input fields use `rounded-md` (8px).
- **The Orb:** The central AI voice visualization is a perfect circle, representing the holistic and fluid nature of sound.
- **Selection States:** Use subtle rounded-rectangles for list item highlights, never sharp corners.

## Components
- **Primary Button:** Solid #E8A87C background with #12100E text. No shadow; uses a subtle scale-down effect (0.98) on press.
- **Interrupt Button:** A circular button with #E85D4E background. Contains a "Stop" icon. Pulses slightly when the AI is speaking.
- **Glass Cards:** Must feature the 16px blur and 1px border. Used for lesson modules, transcript segments, and settings panels.
- **Voice Orb:** A dynamic SVG/Canvas element using the Amber (#E8A87C) color with a varying Gaussian blur (20px-40px) to simulate glowing light that reacts to voice frequency.
- **Inputs:** Darker than the background (#0A0908), 1px border, with #F5F2EB text. Focused state changes border to Amber.
- **Chips/Labels:** JetBrains Mono, uppercase, with a #2A241F background and #A0988E text.
- **Telemetry Readout:** Small, monospaced text strings in the corners of the viewport to show "Live Connection" or "Latency: 24ms."