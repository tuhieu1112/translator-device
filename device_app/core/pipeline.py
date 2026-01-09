from __future__ import annotations

import time
import re
from typing import Any

from device_app.core.modes import Mode


def _strip_music_marks(text: str) -> str:
    """
    Xóa các ký tự nhạc (ví dụ: ♪ ♫ ♩ ♬ …) xuất hiện ở đầu/đuôi
    của chuỗi do NMT/opus chèn vào, tránh gây nhiễu cho TTS.
    Chỉ làm sạch đầu và cuối, KHÔNG sửa nội dung giữa chuỗi.
    """
    if not text:
        return text
    # tập các ký tự nhạc phổ biến: U+2669..U+266F plus common music symbols
    music_chars = r"\u2669\u266A\u266B\u266C\u266D\u266E\u266F\u1F3B5\u1F3B6"
    # xóa liên tiếp các ký tự nhạc + whitespace ở đầu và cuối
    text = re.sub(rf"^[{music_chars}\s]+", "", text)
    text = re.sub(rf"[{music_chars}\s]+$", "", text)
    return text.strip()


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
        self._talk_pressed_prev = False

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
    # TALK BUTTON (EDGE)
    # ==================================================

    def _safe_talk_button(self) -> None:
        try:
            pressed = self.buttons.is_talk_pressed()

            if pressed and not self._talk_pressed_prev and self.state == "READY":
                self._talk_pressed_prev = True
                self._handle_talk_start()

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
            self._back_to_ready()
            return

        # ================= TRANSLATE =================
        try:
            self.state = "TRANSLATING"
            self.display.show_status(mode=self.mode, state="TRANSLATING")

            # -------- STT --------
            if self.mode == Mode.VI_EN:
                text_in = self.stt_vi.transcribe_file(wav_path)
            else:
                text_in = self.stt_en.transcribe_file(wav_path)

            print("[STT] Text in:", repr(text_in))

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
                # ===== SKELETON EXTRACT =====
                skel, slots = self.skeleton.extract_vi(result["text"])
                print("[SKELETON][VI] skel =", skel)
                print("[SKELETON][VI] slots =", slots)

                # ===== MAKE NMT-SAFE TOKENS =====
                safe_skel = skel
                safe_slots = {}

                for ph, value in slots.items():
                    # ví dụ ph = "[PN0]"
                    name = re.sub(r"^\[|\]$", "", ph)  # PN0
                    safe_token = f"PN_{name}"  # PN_PN0

                    safe_skel = safe_skel.replace(ph, safe_token)
                    safe_slots[safe_token] = value

                print("[SKELETON][VI] safe_skel =", safe_skel)
                print("[SKELETON][VI] safe_slots =", safe_slots)

                # ===== NMT =====
                print("[NMT][VI->EN] input :", safe_skel)
                translated = self.nmt_vi_en.translate(safe_skel)
                print("[NMT][VI->EN] output:", translated)

                # ===== COMPOSE BACK =====
                text_out = self.skeleton.compose(translated, safe_slots)
                print("[FINAL][EN]:", text_out)

                # --- strip music marks only ---
                text_out = _strip_music_marks(text_out)
                print("[FINAL][EN][CLEAN]:", repr(text_out))

                self.tts_en.speak(text_out)

            else:
                # ===== EN -> VI (BỎ skeleton HOÀN TOÀN) =====
                src_text = result["text"]
                print("[NMT][EN->VI] input :", src_text)

                translated = self.nmt_en_vi.translate(src_text)
                print("[NMT][EN->VI] output:", translated)

                # --- strip music marks only ---
                translated = _strip_music_marks(translated)
                print("[FINAL][VI][CLEAN]:", repr(translated))

                self.tts_vi.speak(translated)

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
