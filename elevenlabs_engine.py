import os
import re
import queue
import ctypes
import threading
import tempfile
import requests
import pyttsx3

class ElevenLabsVoiceEngine:
    def __init__(self, api_key: str, voice_id: str = "pNInz6obpgDQGcFmaJgB", enabled: bool = True):
        self.api_key = api_key
        self.voice_id = voice_id # Adam
        self.enabled = enabled
        self.queue = queue.Queue()
        self.is_speaking = False
        self.current_alias = None
        self.on_speech_started = None
        self.on_speech_finished = None

        try:
            self.fallback_engine = pyttsx3.init()
            self.fallback_engine.setProperty('rate', 165)
        except Exception:
            self.fallback_engine = None

        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def set_callbacks(self, on_start, on_finish):
        self.on_speech_started = on_start
        self.on_speech_finished = on_finish

    def clean_text(self, text: str) -> str:
        text = re.sub(r'[\*#_`~\[\]\(\)<>]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def stop(self):
        """Immediately interrupt and stop all currently playing and queued speech."""
        try:
            # Drain queue
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                    self.queue.task_done()
                except Exception:
                    break

            # Stop Windows MCI audio immediately
            winmm = ctypes.windll.winmm
            if self.current_alias:
                winmm.mciSendStringW(f'stop {self.current_alias}', None, 0, 0)
                winmm.mciSendStringW(f'close {self.current_alias}', None, 0, 0)
            winmm.mciSendStringW('stop all', None, 0, 0)

            # Stop fallback engine
            if self.fallback_engine:
                try:
                    self.fallback_engine.stop()
                except Exception:
                    pass

            self.is_speaking = False
            if self.on_speech_finished:
                try: self.on_speech_finished()
                except Exception: pass
        except Exception as e:
            print(f"Error stopping speech: {e}")

    def _play_audio_file(self, file_path: str):
        try:
            winmm = ctypes.windll.winmm
            self.current_alias = f"mp3_{threading.get_ident()}"
            winmm.mciSendStringW(f'open "{file_path}" type mpegvideo alias {self.current_alias}', None, 0, 0)
            winmm.mciSendStringW(f'play {self.current_alias} wait', None, 0, 0)
            winmm.mciSendStringW(f'close {self.current_alias}', None, 0, 0)
            self.current_alias = None
        except Exception as e:
            print(f"Audio Playback Error: {e}")

    def _speak_with_elevenlabs(self, clean_txt: str) -> bool:
        if not self.api_key:
            return False

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": clean_txt,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.85,
                "style": 0.15,
                "use_speaker_boost": True
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200 and resp.content:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    temp_path = f.name
                    f.write(resp.content)

                self._play_audio_file(temp_path)
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"ElevenLabs Network Error: {e}")

        return False

    def _speak_fallback(self, clean_txt: str):
        if self.fallback_engine:
            try:
                self.fallback_engine.say(clean_txt)
                self.fallback_engine.runAndWait()
            except Exception as e:
                print(f"Local TTS Error: {e}")

    def _process_queue(self):
        while True:
            text = self.queue.get()
            if text is None:
                break

            if self.enabled and text.strip():
                clean_txt = self.clean_text(text)
                if clean_txt:
                    self.is_speaking = True
                    if self.on_speech_started:
                        try: self.on_speech_started()
                        except Exception: pass

                    success = self._speak_with_elevenlabs(clean_txt)
                    if not success:
                        self._speak_fallback(clean_txt)

                    self.is_speaking = False
                    if self.on_speech_finished:
                        try: self.on_speech_finished()
                        except Exception: pass

            self.queue.task_done()

    def speak(self, text: str):
        if self.enabled and text:
            self.queue.put(text)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled
