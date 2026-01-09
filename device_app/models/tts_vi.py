from __future__ import annotations
from device_app.models.piper_tts import PiperTTS


class TTSVi(PiperTTS):
    def __init__(self, config: dict):
        # PiperTTS KHÔNG nhận tham số
        super().__init__()

        self.voice = config["TTS"]["VI"]["VOICE"]
        self.piper_exe = config["TTS"]["VI"]["PIPER_EXE"]
