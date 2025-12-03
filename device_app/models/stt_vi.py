# device_app/models/stt_vi.py

class STTVi:
    def __init__(self, config):
        self.config = config

    def transcribe(self, wav_path: str) -> str:
        # Stub: giả lập nhận dạng tiếng Việt
        return "xin chao, toi la thiet bi phien dich"
