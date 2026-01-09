# device_app/models/tts_en.py
from __future__ import annotations

from .piper_tts import PiperTTS


class TTSEn(PiperTTS):
    """
    English TTS wrapper
    Backend: Piper
    Output: WAV file (native Piper sample rate, usually 22050 Hz)
    """

    def __init__(self, config: dict) -> None:
        super().__init__(
            config=config,
            lang="en",
            model_path=config["TTS"]["EN"]["MODEL_PATH"],
            speaker_id=config["TTS"]["EN"].get("SPEAKER_ID", 0),
        )
