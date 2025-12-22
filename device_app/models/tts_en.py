# device_app/models/tts_en.py
from __future__ import annotations

from typing import Any, Mapping

from device_app.models.tts_base import TTSBase


class TTSEn(TTSBase):
    """TTS tiếng Anh dùng Piper."""

    def __init__(self, config: Mapping[str, Any]) -> None:
        # key "EN" trong config["TTS"]
        super().__init__(config=config, tts_key="EN", lang="en")
