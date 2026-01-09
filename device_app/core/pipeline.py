from __future__ import annotations

import time
from typing import Any

from device_app.core.modes import Mode


class TranslatorPipeline:
    """
    Central translator pipeline (SAFE VERSION).

    Design goals:
    - Never block main loop
    - Hardware failure tolerant
    - DEV mode friendly
    """

    def __init__(
        self,
        *,
        config: dict | None = None,
        display: Any,
        buttons: Any,
        audio: Any,
        power: Any,
        stt_en: Any | None = None,
        stt_vi: Any | None = None,
        nmt_en_vi: Any | None = None,
        nmt_vi_en: Any | None = None,
        tts_en: Any | None = None,
        tts_vi: Any | None = None,
        nlp_en: Any | None = None,
        nlp_vi: Any | None = None,
        skeleton: Any | None = None,
        device_env: str = "DEV",
    ) -> None:
        self.config = config or {}

        # hardware
        self.display = display
        self.buttons = buttons
        self.audio = audio
        self.power = power

        # models (optional in DEV)
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
        if self.device_env == "DEV":
            print("[PIPELINE] DEV mode: models are mocked / optional")
        else:
            assert self.stt_en and self.stt_vi
            assert self.nmt_en_vi and self.nmt_vi_en
            assert self.tts_en and self.tts_vi
            assert self.nlp_en and self.nlp_vi and self.skeleton
            print("[PIPELINE] All models loaded")

        print("[PIPELINE] Ready")

    # ==========================================================
    # MAIN LOOP (NON-BLOCKING)
    # ==========================================================

    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = "READY"

        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass

        print("[PIPELINE] Device loop started:", self.mode)

        while True:
            # ---------- POWER ----------
            try:
                pct = self.power.get_percent()
                getattr(self.display, "show_battery", lambda *_: None)(pct)
            except Exception:
                pass

            try:
                if self.power.is_low():
                    self.display.show_status("Pin yếu — tắt máy")
                    self.power.shutdown()
                    return
            except Exception:
                pass

            # ---------- MODE ----------
            try:
                evt = self.buttons.poll_mode_event()
                if evt == "short":
                    self._toggle_mode()
                elif evt == "long":
                    self.display.show_status("Tắt thiết bị")
                    self.power.shutdown()
                    return
            except Exception:
                pass

            # ---------- TALK ----------
            try:
                if self.buttons.is_talk_pressed():
                    self._handle_talk_safe()
            except Exception as e:
                print("[TALK] error:", e)

            time.sleep(0.05)

    # ==========================================================
    # MODE
    # ==========================================================

    def _toggle_mode(self) -> None:
        self.mode = Mode.EN_VI if self.mode == Mode.VI_EN else Mode.VI_EN
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass
        print("[MODE] Switched to", self.mode)

    # ==========================================================
    # TALK FLOW (SAFE VERSION)
    # ==========================================================

    def _handle_talk_safe(self) -> None:
        self.state = "RECORDING"
        self.display.show_status("Đang nghe...", mode=self.mode, state=self.state)

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            self._back_to_ready()
            return

        start = time.time()
        MAX_HOLD = 15.0  # anti-freeze watchdog

        while True:
            try:
                if not self.buttons.is_talk_pressed():
                    break
                if time.time() - start > MAX_HOLD:
                    print("[TALK] timeout")
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

        # ---------- DEV MODE ----------
        if self.device_env == "DEV":
            self.state = "READY"
            self.display.show_mode(self.mode)
            return

        # ---------- TRANSLATE ----------
        self.state = "TRANSLATING"
        self.display.show_status("Đang dịch...", mode=self.mode, state=self.state)

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
            self._back_to_ready()
            return

        try:
            if self.mode == Mode.VI_EN:
                skel, slots = self.skeleton.extract_vi(result["text"])
            else:
                skel, slots = self.skeleton.extract_en(result["text"])
        except Exception:
            skel, slots = result["text"], {}

        try:
            translated = (
                self.nmt_vi_en.translate(skel)
                if self.mode == Mode.VI_EN
                else self.nmt_en_vi.translate(skel)
            )
        except Exception as e:
            print("[NMT] error:", e)
            self._back_to_ready()
            return

        try:
            text_out = self.skeleton.compose(translated, slots)
        except Exception:
            text_out = translated

        # ---------- SPEAK ----------
        self.state = "SPEAKING"
        self.display.show_status("Đang phát...", mode=self.mode, state=self.state)

        try:
            if self.mode == Mode.VI_EN:
                self.tts_en.speak(text_out)
            else:
                self.tts_vi.speak(text_out)
        except Exception as e:
            print("[TTS] error:", e)

        self._back_to_ready()

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _back_to_ready(self) -> None:
        self.state = "READY"
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass
