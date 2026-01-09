# device_app/models/tts_en.py
from __future__ import annotations

from device_app.models.piper_tts import PiperTTS


class TTSEn(PiperTTS):
    def __init__(self, config: dict):
        cfg = config["TTS"]["EN"]

        super().__init__(
            cfg["MODEL_PATH"],
            cfg["PIPER_EXE"],
        )
