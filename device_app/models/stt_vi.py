# device_app/models/stt_vi.py

from pathlib import Path
from .stt_base import BaseSTT


class STTVi(BaseSTT):
    """
    Stub STT tiếng Việt.
    Sau này bạn thay phần transcribe() bằng model thật (onnx, HF...).
    """

    def __init__(self, config):
        super().__init__(config, lang="vi")
        print("[STT VI] Using STUB backend (real model disabled).")

    def transcribe(self, wav_path: str | Path) -> str:
        # TODO: sau này đọc file wav_path và chạy model thật
        # Hiện tại trả về câu giả để pipeline chạy được
        return "xin chao, toi la thiet bi phien dich"
