# device_app/models/stt_base.py

from abc import ABC, abstractmethod
from pathlib import Path


class BaseSTT(ABC):
    """Interface chung cho mọi backend STT (onnx, HF, vosk...)."""

    def __init__(self, config, lang: str):
        self.config = config
        self.lang = lang

    @abstractmethod
    def transcribe(self, wav_path: str | Path) -> str:
        raise NotImplementedError
