# device_app/models/stt_en.py

from pathlib import Path
from .stt_base import BaseSTT


class STTEn(BaseSTT):
    """
    Stub STT tiếng Anh.
    Sau này thay transcribe() bằng model thật.
    """

    def __init__(self, config):
        super().__init__(config, lang="en")
        print("[STT EN] Using STUB backend (real model disabled).")

    def transcribe(self, wav_path: str | Path) -> str:
        # TODO: sau này đọc file wav_path và chạy model thật
        return "hello, i am the translator device"
