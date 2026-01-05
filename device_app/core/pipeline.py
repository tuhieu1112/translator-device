from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import time
import os

from device_app.core.modes import Mode


@dataclass
class TranslatorPipeline:
    config: Any
    display: Any
    buttons: Any
    audio: Any
    power: Any

    stt_en: Any = field(init=False, default=None)
    stt_vi: Any = field(init=False, default=None)
    nmt_en_vi: Any = field(init=False, default=None)
    nmt_vi_en: Any = field(init=False, default=None)
    tts_en: Any = field(init=False, default=None)
    tts_vi: Any = field(init=False, default=None)
    nlp_en: Any = field(init=False, default=None)
    nlp_vi: Any = field(init=False, default=None)
    skeleton: Any = field(init=False, default=None)

    # ================= INIT =================

    def __post_init__(self):
        print("[PIPELINE] Initializing models...")

        # -------- DEV MODE: KHÔNG LOAD MODEL --------
        if os.getenv("DEVICE_ENV") == "DEV":
            print("[PIPELINE] DEV mode - skip model loading")
            return

        # -------- PROD MODE: LOAD MODEL THẬT --------
        from device_app.models.stt_en import STTEn
        from device_app.models.stt_vi import STTVi
        from device_app.models.nmt_en_vi import NMTEnVi
        from device_app.models.nmt_vi_en import NMTViEn
        from device_app.models.tts_en import TTSEn
        from device_app.models.tts_vi import TTSVi
        from device_app.models.nlp.nlp_processor import NLPProcessorV2
        from device_app.models.nlp.skeleton_translation import SkeletonTranslator

        self.stt_en = STTEn(self.config)
        self.stt_vi = STTVi(self.config)

        self.nmt_en_vi = NMTEnVi(self.config)
        self.nmt_vi_en = NMTViEn(self.config)

        self.tts_en = TTSEn(self.config)
        self.tts_vi = TTSVi(self.config)

        self.nlp_en = NLPProcessorV2(lang="en")
        self.nlp_vi = NLPProcessorV2(lang="vi")

        self.skeleton = SkeletonTranslator()

        print("[PIPELINE] Ready")

    # ================= MAIN LOOP =================

    def run(self, start_mode: Mode = Mode.VI_EN):
        mode = start_mode
        self.display.show_mode(mode)

        print("[PIPELINE] Device loop started")

        while True:
            # -------- POWER CHECK --------
            percent = self.power.get_percent()
            self.display.show_battery(percent)

            if self.power.is_low():
                print("[POWER] Low battery")
                self.power.shutdown()
                return

            # -------- MODE BUTTON --------
            evt = self.buttons.poll_mode_event()
            if evt == "short":
                mode = Mode.EN_VI if mode == Mode.VI_EN else Mode.VI_EN
                self.display.show_mode(mode)
                time.sleep(0.2)
                continue

            if evt == "long":
                print("[POWER] Shutdown requested")
                self.power.shutdown()
                return

            # -------- TALK BUTTON --------
            if not self.buttons.is_talk_pressed():
                time.sleep(0.05)
                continue

            if mode == Mode.VI_EN:
                self._vi_en()
            else:
                self._en_vi()

            time.sleep(0.1)

    # ================= VI → EN =================

    def _vi_en(self):
        self.display.show_status("", Mode.VI_EN, "RECORDING", 100)
        self.audio.start_record()

        while self.buttons.is_talk_pressed():
            time.sleep(0.01)

        wav = self.audio.stop_record()
        self.buttons.release()

        text = (self.stt_vi.transcribe_file(wav) or "").strip()
        print("[STT VI]:", text)

        result = self.nlp_vi.process(text)
        if not result["text"]:
            self.tts_vi.speak(result["fallback"])
            return

        self.display.show_status("", Mode.VI_EN, "TRANSLATING", 100)

        skel, slots = self.skeleton.extract_vi(result["text"])
        en_raw = self.nmt_vi_en.translate(skel)
        out = self.skeleton.compose(en_raw, slots)

        print("[OUT EN]:", out)
        self.tts_en.speak(out)

    # ================= EN → VI =================

    def _en_vi(self):
        self.display.show_status("", Mode.EN_VI, "RECORDING", 100)
        self.audio.start_record()

        while self.buttons.is_talk_pressed():
            time.sleep(0.01)

        wav = self.audio.stop_record()
        self.buttons.release()

        text = (self.stt_en.transcribe_file(wav) or "").strip()
        print("[STT EN]:", text)

        result = self.nlp_en.process(text)
        if not result["text"]:
            self.tts_en.speak(result["fallback"])
            return

        self.display.show_status("", Mode.EN_VI, "TRANSLATING", 100)

        skel, slots = self.skeleton.extract_en(result["text"])
        vi_raw = self.nmt_en_vi.translate(skel)
        out = self.skeleton.compose(vi_raw, slots)

        print("[OUT VI]:", out)
        self.tts_vi.speak(out)
