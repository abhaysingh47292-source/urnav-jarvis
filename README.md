# Urnav // Jarvis Dynamic Island Workstation Copilot

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-brightgreen?style=for-the-badge&logo=qt)](https://www.qt.io/)
[![Ollama](https://img.shields.io/badge/Local_AI-Qwen%202.5%201.5B-orange?style=for-the-badge&logo=ollama)](https://ollama.com/)
[![Gemini](https://img.shields.io/badge/Cloud_AI-Gemini%203.5%20Flash-blueviolet?style=for-the-badge&logo=google)](https://deepmind.google/technologies/gemini/)
[![Voice](https://img.shields.io/badge/Voice-ElevenLabs%20Neural-black?style=for-the-badge)](https://elevenlabs.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **An autonomous, floating Dynamic Island desktop intelligence that lives at the top of your Windows workstation.**
> Seamlessly blends fluid Apple/Celestia notch physics, Google Gemini-style animated particle light waves, unlimited offline local LLM intelligence, voice interaction, document summarization, and direct 1-click GitHub publishing.

---

## ⚡ Overview

Urnav sits flush at the very top of your primary display as an ultra-compact OLED-matte pill notch. It silently monitors your workstation, displays real-time telemetry, and smoothly expands into a 4-quadrant executive intelligence HUD upon cursor hover or pressing **`Alt + Space`**.

When you move your mouse away, Urnav automatically glides back into its sleek notch after 5 seconds of inactivity.

---

## 🚀 Key Capabilities

### 1. 🏝️ Fluid Dynamic Notch Physics
- **Compact Pill Mode (Idle)**: Sits flush at `y = 0` (380x42px). Displays status dot, live time, mini Gemini particle ribbon, CPU/Battery telemetry, and micro-controls.
- **Hover Expansion**: Simply hover your cursor over the notch to smoothly expand the full 820x560px multi-dashboard (`QPropertyAnimation` with cubic easing).
- **Auto-Collapse**: Automatically animates back into the notch after 5 seconds outside.
- **Pin Mode (`[PIN]`)**: Lock the dashboard open while studying, coding, or reading.
- **Global Hotkey (`Alt + Space`)**: Toggle expand/collapse from anywhere in Windows.

### 2. 🌌 Gemini Animated Particle Wave (`gemini_particles.py`)
- Custom 40 FPS hardware-accelerated QPainter particle canvas.
- Renders glowing floating solar particles (`#FF6B00` & `#FFFFFF`) and an undulating light ribbon across the interface.
- **Adaptive State Reactive**:
  - `IDLE`: Gentle breathing aura and drifting star motes.
  - `LISTENING`: Dynamic surge in particle frequency and amplitude.
  - `THINKING`: Concentrated orbital wave ribbon during inference.
  - `SPEAKING`: Rhythmic harmonic audio wave reacting to voice playback.

### 3. 🧠 Hybrid Dual-Brain Architecture
- **Local Primary Engine**: Powered by **Qwen 2.5 1.5B** via local Ollama. Zero rate limits, zero API bills, zero internet dependency.
- **Cloud Failover**: Silent automatic fallback to **Google Gemini 3.5 Flash** for massive multi-modal tasks. 429 quota exhaustion errors are completely intercepted with instant local failover.
- **Natural Voice Synthesis**: Natural conversational speech via **ElevenLabs Neural Audio** (Adam voice). Zero robotic intros or self-identifying technical announcements.
- **Strictly Zero Emojis**: Crisp typographic styling and executive badges (`[*]`, `[SYS]`, `[CPU]`, `[PIN]`, `[MIC]`).

### 4. 📂 Universal Document Ingestion & GitHub Publishing
- **Drag & Drop Directly from File Explorer**: Drag any file onto the Urnav notch or dashboard to ingest it immediately.
- **File Explorer Picker**: One-click file picker or instant *"Use Latest Download"* selector.
- **Multi-Format Extraction**:
  - **PDF Documents**: Page-by-page text extraction and table reading with `pypdf`.
  - **Word Documents**: Heading and paragraph extraction with `python-docx`.
  - **Code & Text**: Python, JavaScript, TypeScript, C++, Java, JSON, SQL, and Markdown.
- **Masterclass Study Notes Synthesis**: Automatically generates structured reports with Executive Summary, Principles & Formulas, Technical Architecture, and Actionable Review Items.
- **1-Click GitHub Sync**: Push generated summaries directly to your GitHub repository using the GitHub REST API (v3) or local git. Displays the direct URL and copies it to your clipboard.

### 5. 🛠️ Workstation Control & Executive Utilities
- **App Launcher Grid**: Instant launch for Google Chrome, VS Code, File Explorer, Windows Terminal, Task Manager, Notepad, and Calculator.
- **Audio Control**: System volume up (`+10%`), volume down (`-10%`), and mute toggle.
- **Screen Snip & Security**: Capture desktop screenshot to `Pictures/Urnav_Captures` and lock workstation (`Win + L`).
- **Dynamic Accent Color**: One-click toggle between signature **Solar Orange** (`#FF6B00`) and your native **Windows System Accent Color**.

---

## 🏛️ Architecture

```
                                  [ Windows Top Notch ]
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
            [ Compact Pill (380x42) ]              [ Expanded HUD (820x560) ]
            • Time & Telemetry                      • Gemini Particle Wave (40 FPS)
            • Quick Mic & Pin                       • Multi-Dashboard Stack
            • Mini Particle Aura                    • Drag & Drop Target
                       │                                         │
                       └────────────────────┬────────────────────┘
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │              DASHBOARD WORKSPACE MODULES                │
               ├───────────────────┬───────────────────┬─────────────────┤
               │  Executive Brief  │    AI Copilot     │ Documents & Git │
               │  • Day Cycle Bar  │    • Voice Rec    │ • Drag-and-Drop │
               │  • System Vitals  │    • Local Brain  │ • PDF/Docx Read │
               │  • Scratchpad     │    • Speech Audio │ • Push to Repo  │
               └───────────────────┴───────────────────┴─────────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
         [ Local Qwen 2.5 1.5B (Ollama) ]         [ Cloud Gemini 3.5 Flash ]
         • Instant offline inference              • High-capacity reasoning
         • Zero quota boundaries                  • Multi-modal analysis
```

---

## 📦 Installation & Quickstart

### Prerequisites
1. **Python 3.10+** (64-bit Windows)
2. **Git for Windows**
3. **Ollama** with Qwen 2.5:
   ```bash
   ollama run qwen2.5:1.5b
   ```

### Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/abhaysingh47292-source/urnav-jarvis.git
   cd urnav-jarvis
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys** (Optional for cloud features):
   Copy `config.example.json` to `config.json`:
   ```bash
   copy config.example.json config.json
   ```
   Add your keys:
   - `gemini_api_key`: Google Gemini API key
   - `elevenlabs_api_key`: ElevenLabs API key
   - `github_repo` & `github_token`: For 1-click GitHub publishing

4. **Launch Urnav**:
   ```bash
   # Run directly
   python main.py

   # Or run detached in background
   run_urnav.bat
   ```

---

## ⌨️ Shortcuts & Controls

| Action | Control / Hotkey |
| :--- | :--- |
| **Toggle HUD Expand / Collapse** | `Alt + Space` |
| **Hover Reveal** | Move mouse over top notch |
| **Pin / Unpin HUD Open** | Click `[PIN]` |
| **Voice Listening** | Click `[MIC]` or press `Alt + Space` -> Voice Button |
| **Silence Voice Speech** | Click `[SILENCE]` or say *"silence"* / *"shut up"* |
| **Drag & Drop File** | Drag any file from Explorer onto Urnav |
| **Push to GitHub** | Click `[PUSH TO GITHUB]` in Documents tab |
| **Switch Accent Color** | Click `SWITCH ACCENT COLOR` in PC Control tab |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
