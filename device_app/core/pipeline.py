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
from device_app.models.nlp.nlp_processor import NLPProcessorV2
from device_app.models.nlp.skeleton_translation import SkeletonTranslator


@dataclass
class TranslatorPipeline:
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

    def __post_init__(self):
        self.stt_en = STTEn(self.config)
        self.stt_vi = STTVi(self.config)
        self.nmt_en_vi = NMTEnVi(self.config)
        self.nmt_vi_en = NMTViEn(self.config)
        self.tts_en = TTSEn(self.config)
        self.tts_vi = TTSVi(self.config)
        self.nlp_en = NLPProcessorV2(lang="en")
        self.nlp_vi = NLPProcessorV2(lang="vi")
        self.skeleton = SkeletonTranslator()

    # ---------------- ENTRY ----------------

    def run_once(self, mode: Mode):
        if mode == Mode.VI_EN:
            self._vi_en()
        else:
            self._en_vi()

    # ---------------- VI → EN ----------------

    def _vi_en(self):
        self.buttons.wait_talk_press()
        self.audio.start_record()

        while self.buttons.is_talk_pressed():
            pass

        wav = self.audio.stop_record()

        text = (self.stt_vi.transcribe_file(wav) or "").strip()
        result = self.nlp_vi.process(text)

        if not result["text"]:
            self.tts_vi.speak(result["fallback"])
            return

        skel, slots = self.skeleton.extract_vi(result["text"])
        en = self.nmt_vi_en.translate(skel)
        out = self.skeleton.compose(en, slots)
        self.tts_en.speak(out)

    # ---------------- EN → VI ----------------

    def _en_vi(self):
        self.buttons.wait_talk_press()
        self.audio.start_record()

        while self.buttons.is_talk_pressed():
            pass

        wav = self.audio.stop_record()

        text = (self.stt_en.transcribe_file(wav) or "").strip()
        result = self.nlp_en.process(text)

        if not result["text"]:
            self.tts_en.speak(result["fallback"])
            return

        skel, slots = self.skeleton.extract_en(result["text"])
        vi = self.nmt_en_vi.translate(skel)
        out = self.skeleton.compose(vi, slots)
        self.tts_vi.speak(out)
