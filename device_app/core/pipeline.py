# device_app/core/pipeline.py
from __future__ import annotations

import time
from typing import Any

from device_app.core.modes import Mode


class TranslatorPipeline:
    """
    Fault-tolerant translator pipeline.

    - Không bao giờ crash vì phần cứng
    - Power / Display / Button / Audio đều optional
    - DEV mode không load model
    """

    def __init__(
        self,
        *,
        display: Any,
        buttons: Any,
        audio: Any,
        power: Any,
        device_env: str = "DEV",
        # models (giữ nguyên, không động vào)
        stt_en: Any | None = None,
        stt_vi: Any | None = None,
        nmt_en_vi: Any | None = None,
        nmt_vi_en: Any | None = None,
        tts_en: Any | None = None,
        tts_vi: Any | None = None,
        nlp_en: Any | None = None,
        nlp_vi: Any | None = None,
        skeleton: Any | None = None,
    ) -> None:
        self.display = display
        self.buttons = buttons
        self.audio = audio
        self.power = power

        self.stt_en = stt_en
        self.stt_vi = stt_vi
        self.nmt_en_vi = nmt_en_vi
        self.nmt_vi_en = nmt_vi_en
        self.tts_en = tts_en
        self.tts_vi = tts_vi
        self.nlp_en = nlp_en
        self.nlp_vi = nlp_vi
        self.skeleton = skeleton

        self.device_env = (device_env or "DEV").upper()

        self.mode: Mode = Mode.VI_EN
        self.state: str = "READY"

        print("[PIPELINE] Initializing pipeline")
        print("[PIPELINE] Device env:", self.device_env)
        print("[PIPELINE] Ready")

    # =====================================================
    # MAIN LOOP (TUYỆT ĐỐI KHÔNG TREO)
    # =====================================================

    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = "READY"

        self._safe_display_mode()

        print("[PIPELINE] Device loop started. Mode:", self.mode)

        while True:
            self._safe_power_check()
            self._safe_mode_button()
            self._safe_talk_button()

            time.sleep(0.05)

    # =====================================================
    # SAFE HELPERS (KHÔNG ĐƯỢC CRASH)
    # =====================================================

    def _safe_display_mode(self) -> None:
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass

    def _safe_display_status(self, text: str) -> None:
        try:
            self.display.show_status(
                mode=self.mode,
                state=text,
                battery=self._safe_battery_percent(),
            )
        except Exception:
            pass

    def _safe_battery_percent(self) -> int | None:
        try:
            return self.power.get_percent()
        except Exception:
            return None

    # =====================================================
    # POWER
    # =====================================================

    def _safe_power_check(self) -> None:
        try:
            pct = self.power.get_percent()
            try:
                self.display.show_battery(pct)
            except Exception:
                pass

            if self.power.is_low():
                self._safe_display_status("PIN YEU")
                time.sleep(1)
                self.power.shutdown()
        except Exception:
            # TUYỆT ĐỐI không cho power làm chết pipeline
            pass

    # =====================================================
    # MODE BUTTON
    # =====================================================

    def _safe_mode_button(self) -> None:
        try:
            evt = self.buttons.poll_mode_event()
            if evt == "short":
                self._toggle_mode()
            elif evt == "long":
                self._safe_display_status("TAT MAY")
                time.sleep(0.5)
                self.power.shutdown()
        except Exception:
            pass

    def _toggle_mode(self) -> None:
        self.mode = Mode.EN_VI if self.mode == Mode.VI_EN else Mode.VI_EN
        self._safe_display_mode()
        print("[MODE] Switched to", self.mode)

    # =====================================================
    # TALK FLOW
    # =====================================================

    def _safe_talk_button(self) -> None:
        try:
            if self.buttons.is_talk_pressed():
                self._handle_talk()
        except Exception:
            pass

    def _handle_talk(self) -> None:
        # -------- RECORD --------
        self.state = "RECORDING"
        self._safe_display_status("DANG NGHE")

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            self._back_to_ready()
            return

        while True:
            try:
                if not self.buttons.is_talk_pressed():
                    break
            except Exception:
                break
            time.sleep(0.02)

        try:
            wav_path = self.audio.stop_record()
        except Exception as e:
            print("[AUDIO] stop_record failed:", e)
            self._back_to_ready()
            return

        # -------- DEV MODE --------
        if self.device_env == "DEV":
            self.state = "SPEAKING"
            self._safe_display_status("DEV MODE")
            time.sleep(0.5)
            self._back_to_ready()
            return

        # -------- TRANSLATE --------
        self.state = "TRANSLATING"
        self._safe_display_status("DANG DICH")

        try:
            text_in = (
                self.stt_vi.transcribe(wav_path)
                if self.mode == Mode.VI_EN
                else self.stt_en.transcribe(wav_path)
            )
        except Exception as e:
            print("[STT] error:", e)
            self._back_to_ready()
            return

        try:
            nlp = self.nlp_vi if self.mode == Mode.VI_EN else self.nlp_en
            result = nlp.process(text_in)
        except Exception as e:
            print("[NLP] error:", e)
            result = {"ok": False, "fallback": ""}

        if not result.get("ok"):
            self._speak_fallback(result.get("fallback", ""))
            self._back_to_ready()
            return

        try:
            if self.mode == Mode.VI_EN:
                skel, slots = self.skeleton.extract_vi(result["text"])
                translated = self.nmt_vi_en.translate(skel)
            else:
                skel, slots = self.skeleton.extract_en(result["text"])
                translated = self.nmt_en_vi.translate(skel)

            text_out = self.skeleton.compose(translated, slots)
        except Exception as e:
            print("[NMT] error:", e)
            self._back_to_ready()
            return

        # -------- SPEAK --------
        self.state = "SPEAKING"
        self._safe_display_status("DANG PHAT")

        try:
            if self.mode == Mode.VI_EN:
                self.tts_en.speak(text_out)
            else:
                self.tts_vi.speak(text_out)
        except Exception as e:
            print("[TTS] error:", e)

        self._back_to_ready()

    # =====================================================
    # HELPERS
    # =====================================================

    def _speak_fallback(self, text: str) -> None:
        try:
            if self.mode == Mode.VI_EN:
                self.tts_vi.speak(text)
            else:
                self.tts_en.speak(text)
        except Exception:
            pass

    def _back_to_ready(self) -> None:
        self.state = "READY"
        self._safe_display_mode()
