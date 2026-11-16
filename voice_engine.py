import threading
import queue
import pyttsx3

class UltronVoiceEngine:
    def __init__(self, enabled=True, rate=160, volume=0.9):
        self.enabled = enabled
        self.rate = rate
        self.volume = volume
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _process_queue(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate)
            engine.setProperty('volume', self.volume)
            # Find a male voice if available for Ultron's deep tone
            voices = engine.getProperty('voices')
            for v in voices:
                if 'david' in v.name.lower() or 'male' in v.name.lower():
                    engine.setProperty('voice', v.id)
                    break
        except Exception as e:
            print(f"TTS Engine Init Error: {e}")
            return

        while True:
            text = self.queue.get()
            if text is None:
                break
            if self.enabled and text.strip():
                try:
                    # Clean up markdown formatting symbols before speaking
                    clean_text = text.replace('*', '').replace('#', '').replace('`', '').replace('⚙️', '').replace('🌐', '')
                    engine.say(clean_text)
                    engine.runAndWait()
                except Exception as e:
                    print(f"TTS Speech Error: {e}")
            self.queue.task_done()

    def speak(self, text: str):
        if self.enabled:
            self.queue.put(text)

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def is_enabled(self) -> bool:
        return self.enabled
