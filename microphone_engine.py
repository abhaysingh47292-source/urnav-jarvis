import io
import wave
import sounddevice as sd
import speech_recognition as sr
from PySide6.QtCore import QThread, Signal

class VoiceListenerThread(QThread):
    transcription_ready = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, duration_sec=4.0, sample_rate=16000):
        super().__init__()
        self.duration_sec = duration_sec
        self.sample_rate = sample_rate

    def run(self):
        try:
            self.status_changed.emit("RECORDING AUDIO")
            frames = []

            def callback(indata, frame_count, time_info, status):
                frames.append(bytes(indata))

            # Raw streaming without numpy
            with sd.RawInputStream(samplerate=self.sample_rate, channels=1, dtype='int16', callback=callback):
                sd.sleep(int(self.duration_sec * 1000))

            self.status_changed.emit("TRANSCRIBING")
            audio_bytes = b"".join(frames)
            if not audio_bytes:
                self.error_occurred.emit("No audio frames recorded.")
                return

            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_bytes)
            wav_io.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data)
            if text and text.strip():
                self.transcription_ready.emit(text.strip())
            else:
                self.error_occurred.emit("No clear voice detected.")

        except sr.UnknownValueError:
            self.error_occurred.emit("Could not interpret speech audio.")
        except sr.RequestError as e:
            self.error_occurred.emit(f"Speech service error: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Microphone exception: {e}")
