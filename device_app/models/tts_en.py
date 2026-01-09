from __future__ import annotations
from device_app.models.piper_tts import PiperTTS


class TTSEn(PiperTTS):
    def __init__(self, config: dict):
        super().__init__()

        self.voice = config["TTS"]["EN"]["VOICE"]
        self.piper_exe = config["TTS"]["EN"]["PIPER_EXE"]
