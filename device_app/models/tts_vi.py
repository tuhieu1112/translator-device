from __future__ import annotations
from device_app.models.piper_tts import PiperTTS


class TTSVi(PiperTTS):
    def __init__(self, config: dict):
        super().__init__(
            model_path=config["TTS"]["VI"]["MODEL_PATH"],
            piper_exe=config["TTS"]["VI"]["PIPER_EXE"],
        )
