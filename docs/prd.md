# PRD & Technical Architecture Specification: Local AI English Voice Tutor (Cursor Master Guide)

## 1. Project Overview & Objectives
- **Project Name:** Eloquence (local voice English tutor)
- **Goal:** Build a 100% local, zero-subscription, ultra-low-latency (~1.5–2s voice-to-voice) English tutor designed to take a Spanish native speaker from intermediate (B1/B2) to advanced/professional fluency (C1).
- **Core Philosophy:** In-depth conversational immersion, real-time non-disruptive visual feedback, shadowing/pronunciation exercises, and C1 professional roleplay without cloud API costs or data privacy concerns.

---

## 2. Target Hardware & Resource Allocation Plan
- **Primary GPU:** NVIDIA GeForce RTX 3060 (12 GB VRAM).
- **VRAM Budget Allocation (~8.5 GB - 10.0 GB Total):**
  - **STT (Faster-Whisper `medium.en` / `large-v3` in `float16`):** ~2.0 - 3.0 GB VRAM.
  - **LLM (Llama 3.1 8B Instruct / Qwen 2.5 7B / Qwen 2.5 VL 7B in `Q4_K_M` or `Q5_K_M` via Ollama/vLLM):** ~5.5 - 6.5 GB VRAM.
  - **TTS (Kokoro-82M / Piper TTS in PyTorch/ONNX CUDA):** ~0.5 GB VRAM.
  - **Headroom:** ~2.0 - 3.5 GB VRAM reserved for context buffer, system UI, and image processing.

---

## 3. Technology Stack
- **Backend Framework:** Python 3.11+, FastAPI, WebSockets (for bi-directional audio streaming).
- **Speech-to-Text (STT):** `faster-whisper` / `whisper-cuda`.
- **Large Language Model (LLM):** `Ollama` or `vLLM` running `llama3.1:8b-instruct-q5_K_M` or `qwen2.5:7b-instruct-q5_K_M`.
- **Text-to-Speech (TTS):** `Kokoro-82M` (preferred for ultra-realistic quality and speed) or `Piper TTS` (lightweight fallback).
- **Frontend / UI:** Web-based dashboard (React / Next.js or Vite + Vanilla JS / Tailwind CSS) or Electron app.
- **Audio Management:** Web Audio API (MediaRecorder, AudioContext) for client-side recording, VAD (Voice Activity Detection), and audio streaming.

---

## 4. Master System Prompt (Tutor Personality & Logic)

```markdown
# SYSTEM CONTEXT
You are "Eloquence", a native English language tutor and expert linguist specializing in taking Spanish native speakers from Intermediate (B1/B2) to Advanced/Professional (C1) English fluency.

# CORE OBJECTIVES
1. Conduct highly immersive, fluid, and challenging conversations in English.
2. Provide non-disruptive feedback on subtle grammar mistakes, awkward phrasing, and pronunciation issues.
3. Push the user to adopt C1-level vocabulary, phrasal verbs, idioms, and complex sentence structures.

# INTERACTION RULES
1. Primary Language: 100% English. Only switch to brief Spanish explanations if explicitly asked or if the user inserts a Spanish word when stuck.
2. Response Structure:
   - Always respond in natural conversational English. Keep spoken responses concise (1 to 3 short paragraphs) to encourage user speaking time.
   - Embed C1 idioms, phrasal verbs, or professional connectors naturally into your turn.
3. Feedback & Corrections (Output as structured JSON metadata alongside text):
   - Analyze the user's input for:
     a) Grammatical errors or Spanish-transfer mistakes (e.g., prepositions, verb tenses).
     b) Phrasing improvement (B1/B2 phrasing -> C1 professional alternative).
     c) Phonetic/pronunciation flags for tricky words.

# SCENARIO ROLEPLAYS
Regularly offer C1-level professional scenarios:
- Job interviews for senior tech/business roles.
- High-stakes client negotiation & conflict resolution.
- Project pitch & architectural defense.
- Analyzing complex trends, news, or technical diagrams.
```

---

## 5. System Architecture & Audio Pipeline

```
[User Mic] ---> Web Audio API (Client)
                   | (WebSocket Audio Chunk Stream)
                   v
              [FastAPI Backend]
                   |
                   v
            [Faster-Whisper STT]  --> (Transcribed Text)
                   |
                   v
           [LLM Engine (Ollama/vLLM)] --> (Response Text + JSON Feedback)
                   |
                   v
           [Kokoro/Piper TTS Engine] --> (Audio Chunks Stream)
                   |
                   v
[Client Web UI Audio Player & Live Feedback Sidebar]
```

### Key Technical Pipeline Requirements:
1. **Voice Activity Detection (VAD):** Client-side Silero VAD to detect when user stops speaking (silence threshold ~500ms) before sending end-of-turn signal to STT.
2. **Streaming Response (Sentence-level TTS):** The LLM streams text tokens. As soon as a full sentence (`.`, `?`, `!`) is completed, pass it immediately to Kokoro/Piper TTS so audio starts playing while the LLM generates the next sentence. This achieves **< 2.0s total latency**.
3. **Barge-In / Interruption Handling:** If the user clicks "Interrupt" or starts speaking while audio is playing, instantly send a `CANCEL_AUDIO` signal over WebSockets to abort TTS generation and clear client playback queues.

---

## 6. Required UI/UX Features (Inspired by Codybot)

1. **Main Chat & Audio Interface:**
   - Visualizer/orb for active recording & playback states.
   - Big "Interrupt / Stop Speaking" button.
   - Real-time live transcript of both User and AI speech.
2. **"Listen & Repeat" (Shadowing) Module:**
   - When the LLM/STT flags a mispronounced or misarticulated phrase, render a dedicated card.
   - Highlight mispronounced words in red.
   - Native audio playback button for target phrase + microphone button for user retry.
3. **Sidebar Analytics ("Active Memory"):**
   - **Words/Phrases to Polish:** History of recurring user errors.
   - **Vocabulary Mastered:** Log of C1 terms successfully integrated by user.
4. **C1 Module Selector:**
   - Quick launcher for specific practice domains: *Business Negotiations*, *Interview Prep*, *Phrasal Verbs in Tech*, *System Architecture Defense*.

---

## 7. Step-by-Step Cursor Development Plan

### Phase 1: Local Model Setup & Inferences Test
- Set up local python environment with CUDA support (`torch`, `faster-whisper`, `kokoro-onnx` or `piper-tts`).
- Ensure Ollama is running with `llama3.1:8b` or `qwen2.5:7b`.
- Create a test script verifying that STT + LLM + TTS pipeline executes in under 2 seconds on the RTX 3060 12GB.

### Phase 2: FastAPI Backend & WebSockets Stream
- Build `main.py` with FastAPI.
- Implement `/ws/audio` WebSocket endpoint for bidirectional audio streaming.
- Wire VAD, STT transcription, LLM streaming, and sentence-chunked TTS streaming.

### Phase 3: Web Frontend Development
- Build clean, dark-mode UI with Tailwind CSS.
- Implement MediaRecorder / Web Audio API WebSocket audio sender.
- Add audio stream receiver & Web Audio API buffer player.
- Add Barge-in (Interruption) event handling.

### Phase 4: Feedback Parsing, Shadowing UI & Memory Tracking
- Configure LLM output parsing (structured JSON for corrections + plain text for speech).
- Implement Shadowing UI component ("Escucha y Repite").
- Add local storage or SQLite persistence for user error tracking and progression metrics.

---

## 8. Final Conclusion & Architecture Summary
- **Feasibility:** 100% verified on RTX 3060 12GB.
- **Cost:** $0/month.
- **Privacy:** 100% local, no internet connection required.
- **Performance Target:** Voice-to-Voice latency ~1.5 - 2.0 seconds.
- **Pedagogical Focus:** Tailored for C1 level progression with active feedback, shadowing, and zero conversational interruptions.
