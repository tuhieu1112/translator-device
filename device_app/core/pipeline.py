# device_app/core/pipeline.py
from __future__ import annotations

import time
from typing import Any

from device_app.core.modes import Mode


class TranslatorPipeline:
    """
    Central translator pipeline.

    Responsibilities:
    - coordinate hardware modules (display, buttons, audio, power)
    - orchestrate STT -> NLP -> Skeleton -> NMT -> compose -> TTS
    - DEV mode skips heavy models (useful for HW bring-up)
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
        self.display = display
        self.buttons = buttons
        self.audio = audio
        self.power = power

        # models
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

        # NOTE: dùng string cho state để KHÔNG phụ thuộc State enum (bạn sẽ tạo sau)
        self.mode: Mode = Mode.VI_EN
        self.state: str = "READY"

        print("[PIPELINE] Initializing pipeline")
        if self.device_env == "DEV":
            print("[PIPELINE] DEV mode: models are optional (mocked)")
        else:
            assert self.stt_en and self.stt_vi, "STT models missing"
            assert self.nmt_en_vi and self.nmt_vi_en, "NMT models missing"
            assert self.tts_en and self.tts_vi, "TTS models missing"
            assert self.nlp_en and self.nlp_vi and self.skeleton, "NLP/Skeleton missing"
            print("[PIPELINE] All models provided")

        print("[PIPELINE] Ready")

    # ================= RUN LOOP =================

    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = "READY"

        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass

        print("[PIPELINE] Device loop started. Mode:", self.mode)

        while True:
            # --- power / battery ---
            try:
                percent = self.power.get_percent()
                getattr(self.display, "show_battery", lambda _: None)(percent)
            except Exception:
                pass

            try:
                if self.power.is_low():
                    self.display.show_status("Pin yếu — tắt máy")
                    self.power.shutdown()
                    return
            except Exception:
                pass

            # --- MODE button ---
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

            # --- TALK button ---
            try:
                if self.buttons.is_talk_pressed():
                    self._handle_talk()
            except Exception:
                pass

            time.sleep(0.05)

    # ================= MODE =================

    def _toggle_mode(self) -> None:
        self.mode = Mode.EN_VI if self.mode == Mode.VI_EN else Mode.VI_EN
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass
        print("[MODE] Switched to", self.mode)

    # ================= TALK FLOW =================

    def _handle_talk(self) -> None:
        # -------- RECORDING --------
        self.state = "RECORDING"
        self.display.show_status("Đang nghe...", mode=self.mode, state=self.state)

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            return

        while self.buttons.is_talk_pressed():
            time.sleep(0.02)

        try:
            wav_path = self.audio.stop_record()
        except Exception as e:
            print("[AUDIO] stop_record failed:", e)
            return

        # -------- TRANSLATING --------
        self.state = "TRANSLATING"
        self.display.show_status("Đang dịch...", mode=self.mode, state=self.state)

        if self.device_env == "DEV":
            text_out = "[DEV] Translation result"
        else:
            # STT
            try:
                text_in = (
                    self.stt_vi.transcribe(wav_path)
                    if self.mode == Mode.VI_EN
                    else self.stt_en.transcribe(wav_path)
                )
            except Exception as e:
                print("[STT] error:", e)
                text_in = ""

            # NLP
            try:
                nlp = self.nlp_vi if self.mode == Mode.VI_EN else self.nlp_en
                result = nlp.process(text_in)
            except Exception as e:
                print("[NLP] error:", e)
                result = {"ok": False, "text": "", "fallback": ""}

            if not result.get("ok"):
                fallback = result.get("fallback", "")
                try:
                    if self.mode == Mode.VI_EN:
                        self.tts_vi.speak(fallback)
                    else:
                        self.tts_en.speak(fallback)
                except Exception:
                    pass
                self._back_to_ready()
                return

            # Skeleton
            try:
                if self.mode == Mode.VI_EN:
                    skel, slots = self.skeleton.extract_vi(result["text"])
                else:
                    skel, slots = self.skeleton.extract_en(result["text"])
            except Exception as e:
                print("[SKELETON] error:", e)
                skel, slots = result["text"], {}

            # NMT
            try:
                translated = (
                    self.nmt_vi_en.translate(skel)
                    if self.mode == Mode.VI_EN
                    else self.nmt_en_vi.translate(skel)
                )
            except Exception as e:
                print("[NMT] error:", e)
                translated = ""

            # Compose
            try:
                text_out = self.skeleton.compose(translated, slots)
            except Exception:
                text_out = translated

        # -------- SPEAKING --------
        self.state = "SPEAKING"
        self.display.show_status("Đang phát...", mode=self.mode, state=self.state)

        if self.device_env != "DEV":
            try:
                if self.mode == Mode.VI_EN:
                    self.tts_en.speak(text_out)
                else:
                    self.tts_vi.speak(text_out)
            except Exception as e:
                print("[TTS] speak error:", e)

        self._back_to_ready()

    # ================= HELPERS =================

    def _back_to_ready(self) -> None:
        self.state = "READY"
        self.display.show_mode(self.mode)
