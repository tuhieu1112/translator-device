# device_app/models/__init__.py
from __future__ import annotations

from .stt_vi import STTVi
from .stt_en import STTEn
from .nmt_vi_en import NMTViEn
from .nmt_en_vi import NMTEnVi
from .tts_vi import TTSVi
from .tts_en import TTSEn
from .grammar_en_en import GrammarEnEn

__all__ = [
    "STTEn",
    "STTVi",
    "NMTEnVi",
    "NMTViEn",
    "GrammarEnEn",
    "TTSVi",
    "TTSEn",
]
