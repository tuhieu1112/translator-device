# device_app/models/tts_vi.py
from __future__ import annotations

from typing import Any, Mapping

from device_app.models.tts_base import TTSBase


class TTSVi(TTSBase):
    """TTS tiếng Việt dùng Piper."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        # key "VI" trong config["TTS"]
        super().__init__(config=config, tts_key="VI", lang="vi")
