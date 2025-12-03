# device_app/models/tts_en.py

class TTSEn:
    def __init__(self, config):
        self.config = config

    def synthesize(self, text_en: str) -> str:
        print(f"[TTS DEBUG EN] Giả lập tạo file WAV từ text: {text_en}")
        return "tts_output_en.wav"
