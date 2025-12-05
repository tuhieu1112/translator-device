# device_app/models/tts_vi.py

from pathlib import Path


class TTSVi:
    """
    Stub TTS tiếng Việt.
    Sau này thay synthesize() bằng model TTS thật.
    """

    def __init__(self, config):
        self.config = config
        print("[TTS VI] Using STUB backend (no real speech).")

    def synthesize(self, text_vi: str) -> str:
        # TODO: generate file WAV thật từ text_vi
        print(f"[TTS DEBUG VI] Giả lập tạo WAV từ text: {text_vi}")
        return str(Path("tts_output_vi.wav"))
