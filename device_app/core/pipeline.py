from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from device_app.core.modes import Mode
from device_app.models.stt_en import STTEn
from device_app.models.stt_vi import STTVi
from device_app.models.nmt_en_vi import NMTEnVi
from device_app.models.nmt_vi_en import NMTViEn
from device_app.models.tts_en import TTSEn
from device_app.models.tts_vi import TTSVi

# NLP (KHÔNG sửa câu)
from device_app.models.nlp.nlp_processor import NLPProcessorV2

# Skeleton slot-based (GIẢI PHÁP CUỐI)
from device_app.models.nlp.skeleton_translation import SkeletonTranslator


@dataclass
class TranslatorPipeline:
    """
    PIPELINE FINAL – SKELETON SLOT-BASED

    - OPUS chỉ dịch skeleton
    - Proper nouns bị loại khỏi input dịch
    - Ghép lại đúng vị trí bằng slot [PNx]
    - Không entity, không map, không token giả
    """

    config: Any
    display: Any
    buttons: Any
    audio: Any
    power: Any

    stt_en: STTEn = field(init=False)
    stt_vi: STTVi = field(init=False)
    nmt_en_vi: NMTEnVi = field(init=False)
    nmt_vi_en: NMTViEn = field(init=False)
    tts_en: TTSEn = field(init=False)
    tts_vi: TTSVi = field(init=False)

    nlp_en: NLPProcessorV2 = field(init=False)
    nlp_vi: NLPProcessorV2 = field(init=False)

    skeleton: SkeletonTranslator = field(init=False)

    # ---------------- INIT ----------------

    def __post_init__(self):
        print("[PIPELINE] Initializing models...")

        # STT
        self.stt_en = STTEn(self.config)
        self.stt_vi = STTVi(self.config)

        # NMT (OPUS)
        self.nmt_en_vi = NMTEnVi(self.config)
        self.nmt_vi_en = NMTViEn(self.config)

        # TTS
        self.tts_en = TTSEn(self.config)
        self.tts_vi = TTSVi(self.config)

        # NLP (chỉ fallback nếu STT rỗng)
        self.nlp_en = NLPProcessorV2(lang="en")
        self.nlp_vi = NLPProcessorV2(lang="vi")

        # Skeleton translator
        self.skeleton = SkeletonTranslator()

        print("[PIPELINE] Ready.")

    # ---------------- helpers ----------------

    def _display(self, mode: Mode, state: str):
        try:
            self.display.show_status(
                text="",
                mode=mode,
                state=state,
                battery=100,
            )
        except Exception:
            pass

    # ---------------- EN → VI ----------------

    def _run_en_vi(self):
        mode = Mode.EN_VI
        self._display(mode, "RECORDING")

        wav = self.audio.record()
        raw = (self.stt_en.transcribe_file(wav) or "").strip()
        print("[STT EN]:", raw)

        result = self.nlp_en.process(raw)
        print("[NLP EN]:", result)

        if not result["text"]:
            self.tts_en.speak(result["fallback"])
            return

        self._display(mode, "TRANSLATING")

        # ---- SKELETON EXTRACT (EN) ----
        skeleton_text, slots = self.skeleton.extract_en(result["text"])
        print("[SKELETON EN]:", skeleton_text)
        print("[SLOTS]:", slots)

        # ---- OPUS TRANSLATE ----
        vi_raw = self.nmt_en_vi.translate(skeleton_text)
        print("[NMT EN→VI RAW]:", vi_raw)

        # ---- COMPOSE ----
        vi = self.skeleton.compose(vi_raw, slots)
        print("[COMPOSED]:", vi)

        self.tts_vi.speak(vi)

    # ---------------- VI → EN ----------------

    def _run_vi_en(self):
        mode = Mode.VI_EN
        self._display(mode, "RECORDING")

        wav = self.audio.record()
        raw = (self.stt_vi.transcribe_file(wav) or "").strip()
        print("[STT VI]:", raw)

        result = self.nlp_vi.process(raw)
        print("[NLP VI]:", result)

        if not result["text"]:
            self.tts_vi.speak(result["fallback"])
            return

        self._display(mode, "TRANSLATING")

        # ---- SKELETON EXTRACT (VI) ----
        skeleton_text, slots = self.skeleton.extract_vi(result["text"])
        print("[SKELETON VI]:", skeleton_text)
        print("[SLOTS]:", slots)

        # ---- OPUS TRANSLATE ----
        en_raw = self.nmt_vi_en.translate(skeleton_text)
        print("[NMT VI→EN RAW]:", en_raw)

        # ---- COMPOSE ----
        en = self.skeleton.compose(en_raw, slots)
        print("[COMPOSED]:", en)

        self.tts_en.speak(en)

    # ---------------- ENTRY ----------------

    def run_once(self, mode: Mode):
        if mode is Mode.EN_VI:
            self._run_en_vi()
        elif mode is Mode.VI_EN:
            self._run_vi_en()
