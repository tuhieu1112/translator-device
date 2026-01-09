# device_app/models/tts_vi.py
from __future__ import annotations

from device_app.models.piper_tts import PiperTTS


class TTSVi(PiperTTS):
    """
    Vietnamese TTS wrapper (Piper backend)
    """

    def __init__(self, config: dict):
        tts_cfg = config["TTS"]["VI"]

        super().__init__(
            model_path=tts_cfg["MODEL_PATH"],
            piper_exe=tts_cfg["PIPER_EXE"],
        )
