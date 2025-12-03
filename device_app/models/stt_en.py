# device_app/models/stt_en.py

class STTEn:
    def __init__(self, config):
        self.config = config

    def transcribe(self, wav_path: str) -> str:
        # Stub: giả lập nhận dạng tiếng Anh
        return "hello, i am the translator device"
