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

        # ===== MODELS =====
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

        self._running = True
        self._talk_pressed_prev = False  # EDGE detect

        print("[PIPELINE] Initializing pipeline")
        print(f"[PIPELINE] Device env = {self.device_env}")
        print("[PIPELINE] Ready")

    # ==================================================
    # MAIN LOOP
    # ==================================================

    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = "READY"
        self._running = True

        self._safe_display_mode()
        print("[PIPELINE] Device loop started:", self.mode)

        while self._running:
            self._safe_power_tick()
            self._safe_mode_button()
            self._safe_talk_button()
            time.sleep(0.02)

    # ==================================================
    # POWER
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
                self._request_shutdown()

        except Exception as e:
            print("[POWER] ignored:", e)

    # ==================================================
    # MODE BUTTON
    # ==================================================

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
                self._request_shutdown()
        except Exception as e:
            print("[BUTTON] mode ignored:", e)

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
    # TALK BUTTON (EDGE + HOLD)
    # ==================================================

    def _safe_talk_button(self) -> None:
        try:
            pressed = self.buttons.is_talk_pressed()

            # ---- PRESS EDGE → START RECORD ----
            if pressed and not self._talk_pressed_prev and self.state == "READY":
                self._talk_pressed_prev = True
                self._handle_talk_start()

            # ---- RELEASE EDGE → STOP RECORD ----
            elif not pressed and self._talk_pressed_prev and self.state == "RECORDING":
                self._talk_pressed_prev = False
                self._handle_talk_stop()

            elif not pressed:
                self._talk_pressed_prev = False

        except Exception as e:
            print("[BUTTON] talk ignored:", e)

    # ==================================================
    # TALK FLOW
    # ==================================================

    def _handle_talk_start(self) -> None:
        print("[TALK] Start")
        self.state = "RECORDING"
        self.display.show_status(mode=self.mode, state="LISTENING")

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            self._back_to_ready()

    def _handle_talk_stop(self) -> None:
        print("[TALK] Stop")

        try:
            wav_path = self.audio.stop_record()
        except Exception as e:
            print("[AUDIO] stop_record failed:", e)
            self._back_to_ready()
            return

        print(f"[AUDIO] WAV saved: {wav_path}")

        if self.device_env == "DEV":
            print("[DEV] Skip translate")
            self._back_to_ready()
            return

        # ================= TRANSLATE =================
        try:
            self.state = "TRANSLATING"
            self.display.show_status(mode=self.mode, state="TRANSLATING")

            # -------- STT --------
            if self.mode == Mode.VI_EN:
                print("[STT] Using VI")
                text_in = self.stt_vi.transcribe_file(wav_path)
            else:
                print("[STT] Using EN")
                text_in = self.stt_en.transcribe_file(wav_path)

            print(f"[STT] Text in: '{text_in}'")

            # -------- NLP --------
            nlp = self.nlp_vi if self.mode == Mode.VI_EN else self.nlp_en
            result = nlp.process(text_in)

            print("[NLP] Result:", result)

            if not result.get("ok"):
                self._speak_fallback(result.get("fallback", ""))
                self._back_to_ready()
                return

            # -------- NMT + TTS --------
            if self.mode == Mode.VI_EN:
                skel, slots = self.skeleton.extract_vi(result["text"])
                print("[SKELETON] VI:", skel, slots)

                translated = self.nmt_vi_en.translate(skel)
                print("[NMT] VI→EN:", translated)

                text_out = self.skeleton.compose(translated, slots)
                print("[FINAL EN]:", text_out)

                self.tts_en.speak(text_out)

            else:
                skel, slots = self.skeleton.extract_en(result["text"])
                print("[SKELETON] EN:", skel, slots)

                translated = self.nmt_en_vi.translate(skel)
                print("[NMT] EN→VI:", translated)

                text_out = self.skeleton.compose(translated, slots)
                print("[FINAL VI]:", text_out)

                self.tts_vi.speak(text_out)

        except Exception as e:
            print("[PIPELINE] talk flow error:", e)

        self._back_to_ready()

    # ==================================================
    # FALLBACK
    # ==================================================

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

    def _request_shutdown(self) -> None:
        print("[SYSTEM] Shutdown requested")
        self._running = False
        try:
            self.power.shutdown()
        except Exception as e:
            print("[SYSTEM] shutdown failed:", e)

    # ==================================================
    # STATE
    # ==================================================

    def _back_to_ready(self) -> None:
        self.state = "READY"
        self._safe_display_mode()
