# device_app/models/nmt_vi_en.py

class NMTViEn:
    """Stub NMT VI→EN: tạm thời không dùng mô hình thật."""

    def __init__(self, config):
        print("[NMT VI→EN] Using STUB model (real model is disabled).")
        self.config = config

    def translate(self, text_vi: str) -> str:
        if not text_vi.strip():
            return ""
        # chỉ để nhìn luồng chạy
        return "[EN_STUB] " + text_vi
