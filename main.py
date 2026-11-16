import os
import sys
import json
import subprocess
import requests
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Qt

from system_tools import SystemTools
from gemini_client import GeminiClient
from elevenlabs_engine import ElevenLabsVoiceEngine
from island_ui import DynamicIslandHUD
from hotkey_listener import GlobalHotkeyListener

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
    return {}

def ensure_ollama_running():
    """Ensure local Ollama service is permanently running for unlimited offline AI."""
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=1)
        if r.status_code == 200:
            return
    except Exception:
        pass

    ollama_dir = r"C:\Users\LENOVO\AppData\Local\Microsoft\WinGet\Packages\Ollama.Ollama.Portable_Microsoft.Winget.Source_8wekyb3d8bbwe"
    ollama_exe = os.path.join(ollama_dir, "ollama.exe")
    if os.path.exists(ollama_exe):
        try:
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                [ollama_exe, "serve"],
                cwd=ollama_dir,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True
            )
            print("Launched detached local Ollama service.")
        except Exception as e:
            print(f"Could not auto-start Ollama: {e}")

def main():
    ensure_ollama_running()
    config = load_config()
    gemini_key = config.get("gemini_api_key", "")
    elevenlabs_key = config.get("elevenlabs_api_key", "sk_af5c544402de713c409b7a36ad1dd9af70bb91107a80fc24")
    model = config.get("gemini_model", "gemini-3.5-flash")
    voice_enabled = config.get("voice_enabled", True)

    # 1. Initialize Subsystems
    tools = SystemTools(config=config)
    voice = ElevenLabsVoiceEngine(api_key=elevenlabs_key, enabled=voice_enabled)
    client = GeminiClient(api_key=gemini_key, model=model, tools_executor=tools)

    # 2. Initialize Qt Application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    island = DynamicIslandHUD(
        gemini_client=client,
        system_tools=tools,
        voice_engine=voice
    )
    island.show()
    island.raise_()
    island.activateWindow()

    # Subtle natural greeting (no tech or robotic announcements)
    if voice_enabled:
        voice.speak("Urnav ready.")

    # 3. Global Hotkey (Alt + Space)
    hotkey = GlobalHotkeyListener()
    hotkey.hotkey_triggered.connect(island.toggle_expand)
    hotkey.start()

    # 4. Windows System Tray
    tray = QSystemTrayIcon()
    tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))
    tray.setToolTip("URNAV Workstation Copilot")

    tray_menu = QMenu()
    toggle_action = QAction("Toggle Dynamic Island (Alt + Space)", tray_menu)
    toggle_action.triggered.connect(island.toggle_expand)

    mic_action = QAction("Activate Voice Microphone", tray_menu)
    mic_action.triggered.connect(island.toggle_microphone)

    silence_action = QAction("Silence Speech & Audio", tray_menu)
    silence_action.triggered.connect(island.silence_everything)

    voice_action = QAction("Toggle Voice Engine", tray_menu)
    def toggle_v():
        is_on = not voice.is_enabled()
        voice.set_enabled(is_on)
    voice_action.triggered.connect(toggle_v)

    theme_action = QAction("Switch Accent Color", tray_menu)
    theme_action.triggered.connect(island.toggle_accent_color)

    reset_action = QAction("Clear Context Memory", tray_menu)
    reset_action.triggered.connect(client.reset_chat)

    quit_action = QAction("Exit Urnav", tray_menu)
    def shutdown():
        hotkey.stop()
        app.quit()
    quit_action.triggered.connect(shutdown)

    tray_menu.addAction(toggle_action)
    tray_menu.addAction(mic_action)
    tray_menu.addAction(silence_action)
    tray_menu.addAction(theme_action)
    tray_menu.addAction(voice_action)
    tray_menu.addAction(reset_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)

    tray.setContextMenu(tray_menu)
    tray.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
