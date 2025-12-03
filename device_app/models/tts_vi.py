# device_app/models/tts_vi.py

class TTSVi:
    def __init__(self, config):
        self.config = config

    def synthesize(self, text_vi: str) -> str:
        print(f"[TTS DEBUG VI] Giả lập tạo file WAV từ text: {text_vi}")
        return "tts_output_vi.wav"
