# device_app/models/nmt_en_vi.py

class NMTEnVi:
    """Stub NMT EN→VI: tạm thời không dùng mô hình thật."""

    def __init__(self, config):
        print("[NMT EN→VI] Using STUB model (real model is disabled).")
        self.config = config

    def translate(self, text_en: str) -> str:
        if not text_en.strip():
            return ""
        return "[VI_STUB] " + text_en
