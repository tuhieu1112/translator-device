from __future__ import annotations

import time
from typing import Any

from device_app.core.modes import Mode


class TranslatorPipeline:
    def __init__(
        self,
        *,
        display: Any,
        buttons: Any,
        audio: Any,
        power: Any,
        device_env: str = "DEV",
        **models,
    ) -> None:
        self.display = display
        self.buttons = buttons
        self.audio = audio
        self.power = power

        # models (GIỮ NGUYÊN)
        self.stt_en = models.get("stt_en")
        self.stt_vi = models.get("stt_vi")
        self.nmt_en_vi = models.get("nmt_en_vi")
        self.nmt_vi_en = models.get("nmt_vi_en")
        self.tts_en = models.get("tts_en")
        self.tts_vi = models.get("tts_vi")
        self.nlp_en = models.get("nlp_en")
        self.nlp_vi = models.get("nlp_vi")
        self.skeleton = models.get("skeleton")

        self.device_env = (device_env or "DEV").upper()
        self.mode: Mode = Mode.VI_EN
        self.state: str = "READY"

        print("[PIPELINE] Initializing pipeline")
        print(f"[PIPELINE] Device env = {self.device_env}")
        print("[PIPELINE] Ready")

    # ==================================================
    # MAIN LOOP
    # ==================================================

    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = "READY"

        self._safe_display_mode()

        print("[PIPELINE] Device loop started:", self.mode)

        while True:
            self._safe_power_tick()
            self._safe_mode_button()
            self._safe_talk_button()
            time.sleep(0.05)

    # ==================================================
    # SAFE WRAPPERS
    # ==================================================

    def _safe_power_tick(self) -> None:
        try:
            pct = self.power.get_percent()
            self.display.show_status(
                mode=self.mode,
                state=self.state,
                battery=pct,
            )

            if self.power.is_low():
                self.display.show_status(
                    mode=self.mode,
                    state="LOW BAT",
                    battery=pct,
                )
                self._safe_shutdown()

        except Exception as e:
            # TUYỆT ĐỐI KHÔNG crash
            print("[POWER] ignored error:", e)

    def _safe_mode_button(self) -> None:
        try:
            evt = self.buttons.poll_mode_event()
            if evt == "short":
                self._toggle_mode()
            elif evt == "long":
                self.display.show_status(
                    mode=self.mode,
                    state="SHUTDOWN",
                )
                self._safe_shutdown()
        except Exception as e:
            print("[BUTTON] mode ignored error:", e)

    def _safe_talk_button(self) -> None:
        try:
            if self.buttons.is_talk_pressed():
                self._safe_handle_talk()
        except Exception as e:
            print("[BUTTON] talk ignored error:", e)

    # ==================================================
    # MODE
    # ==================================================

    def _toggle_mode(self) -> None:
        self.mode = Mode.EN_VI if self.mode == Mode.VI_EN else Mode.VI_EN
        self._safe_display_mode()
        print("[MODE] Switched to", self.mode)

    def _safe_display_mode(self) -> None:
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass

    # ==================================================
    # TALK FLOW (AN TOÀN)
    # ==================================================

    def _safe_handle_talk(self) -> None:
        print("[TALK] Start")

        self.state = "RECORDING"
        self.display.show_status(mode=self.mode, state="LISTENING")

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            self._back_to_ready()
            return

        # chờ nhả nút
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

        # DEV: không chạy model
        if self.device_env == "DEV":
            self.display.show_status(mode=self.mode, state="READY")
            print("[DEV] Talk done")
            return

        # ================== LOGIC DỊCH (GIỮ NGUYÊN) ==================
        try:
            self.state = "TRANSLATING"
            self.display.show_status(mode=self.mode, state="TRANSLATING")

            text_in = (
                self.stt_vi.transcribe(wav_path)
                if self.mode == Mode.VI_EN
                else self.stt_en.transcribe(wav_path)
            )

            nlp = self.nlp_vi if self.mode == Mode.VI_EN else self.nlp_en
            result = nlp.process(text_in)

            if not result.get("ok"):
                self._speak_fallback(result.get("fallback", ""))
                self._back_to_ready()
                return

            if self.mode == Mode.VI_EN:
                skel, slots = self.skeleton.extract_vi(result["text"])
                translated = self.nmt_vi_en.translate(skel)
                text_out = self.skeleton.compose(translated, slots)
                self.tts_en.speak(text_out)
            else:
                skel, slots = self.skeleton.extract_en(result["text"])
                translated = self.nmt_en_vi.translate(skel)
                text_out = self.skeleton.compose(translated, slots)
                self.tts_vi.speak(text_out)

        except Exception as e:
            print("[PIPELINE] talk flow error:", e)

        self._back_to_ready()

    def _speak_fallback(self, text: str) -> None:
        try:
            if self.mode == Mode.VI_EN:
                self.tts_vi.speak(text)
            else:
                self.tts_en.speak(text)
        except Exception:
            pass

    # ==================================================
    # SHUTDOWN
    # ==================================================

    def _safe_shutdown(self) -> None:
        try:
            print("[SYSTEM] Shutdown requested")
            self.power.shutdown()
        except Exception as e:
            print("[SYSTEM] shutdown failed:", e)

    # ==================================================
    # STATE
    # ==================================================

    def _back_to_ready(self) -> None:
        self.state = "READY"
        self._safe_display_mode()
