# device_app/models/tts_vi.py
from __future__ import annotations

import re

from .piper_tts import PiperTTS


class TTSVi(PiperTTS):
    """
    Vietnamese TTS wrapper
    Backend: Piper
    Output: WAV file (native Piper SR, usually 22050 Hz)
    """

    def __init__(self, config: dict) -> None:
        super().__init__(
            config=config,
            lang="vi",
            model_path=config["TTS"]["VI"]["MODEL_PATH"],
            speaker_id=config["TTS"]["VI"].get("SPEAKER_ID", 0),
        )

    # --------------------------------------------------
    # Text normalize (VI cần, EN thì không)
    # --------------------------------------------------
    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip()

        # Chuẩn hoá khoảng trắng
        text = re.sub(r"\s+", " ", text)

        # Piper VI đọc tốt hơn nếu có dấu chấm cuối
        if text[-1] not in ".!?":
            text += "."

        return text

    # --------------------------------------------------
    # Override để thêm normalize
    # --------------------------------------------------
    def synthesize_to_file(self, text: str) -> str:
        text = self._normalize_text(text)
        return super().synthesize_to_file(text)
