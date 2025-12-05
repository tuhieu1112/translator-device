# device_app/models/tts_en.py

from pathlib import Path


class TTSEn:
    """
    Stub TTS tiếng Anh.
    """

    def __init__(self, config):
        self.config = config
        print("[TTS EN] Using STUB backend (no real speech).")

    def synthesize(self, text_en: str) -> str:
        print(f"[TTS DEBUG EN] Giả lập tạo WAV từ text: {text_en}")
        return str(Path("tts_output_en.wav"))
