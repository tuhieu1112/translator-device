# device_app/models/grammar_en.py

class GrammarEn:
    """Stub EN→EN grammar: chỉ giả lập sửa câu."""

    def __init__(self, config):
        print("[GRAMMAR EN→EN] Using STUB model (real grammar model disabled).")
        self.config = config

    def correct(self, text_en: str) -> str:
        if not text_en.strip():
            return ""
        return "[FIXED_STUB] " + text_en
