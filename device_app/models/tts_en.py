from __future__ import annotations
from device_app.models.piper_tts import PiperTTS


class TTSEn(PiperTTS):
    def __init__(self, config: dict):
        super().__init__(
            model_path=config["TTS"]["EN"]["MODEL_PATH"],
            piper_exe=config["TTS"]["EN"]["PIPER_EXE"],
        )
