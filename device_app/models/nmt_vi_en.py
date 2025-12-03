# device_app/models/nmt_vi_en.py

class NMTViEn:
    def __init__(self, config):
        self.config = config

    def translate(self, text_vi: str) -> str:
        # Stub: chỉ để bạn thấy luồng chạy
        return "[EN] " + text_vi.upper()
