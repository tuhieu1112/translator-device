# device_app/models/nmt_en_vi.py

class NMTEnVi:
    def __init__(self, config):
        self.config = config

    def translate(self, text_en: str) -> str:
        return "[VI] " + text_en.lower()
