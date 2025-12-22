# device_app/models/nlp/nlp_postprocess.py

from __future__ import annotations


class NLPProcessorV2:
    """
    NLP POST-PROCESSOR – FINAL (GIAO TIẾP THỰC TẾ)

    - KHÔNG sửa câu
    - KHÔNG chặn dịch
    - KHÔNG rule
    - KHÔNG entity
    - CHỈ fallback khi STT rỗng
    """

    def __init__(self, lang: str):
        self.lang = lang

    def process(self, text: str) -> dict:
        text = (text or "").strip()

        # ❌ STT rỗng → yêu cầu nói lại
        if not text:
            return {
                "ok": False,
                "text": "",
                "confidence": 0.0,
                "fallback": (
                    "Please say again" if self.lang == "en" else "Bạn nói lại giúp mình"
                ),
            }

        # ✅ Có text → LUÔN CHO DỊCH
        return {
            "ok": True,
            "text": text,
            "confidence": 0.6,  # chỉ để log
        }
