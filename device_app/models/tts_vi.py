from __future__ import annotations
from device_app.models.piper_tts import PiperTTS


class TTSVi(PiperTTS):
    def __init__(self, config: dict):
        super().__init__(
            model=config["TTS"]["VI"]["MODEL_PATH"],
            voice=None,
            piper_exe=config["TTS"]["VI"]["PIPER_EXE"],
        )
