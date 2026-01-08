# device_app/core/pipeline.py
from __future__ import annotations

import time
from typing import Any

from device_app.core.modes import Mode, State  # assumes Mode/State are defined here


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
        # MODEL OBJECTS: provide these when device_env != "DEV"
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

        # Models
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
        self.state: State = State.READY

        print("[PIPELINE] Initializing pipeline")
        if self.device_env == "DEV":
            print("[PIPELINE] DEV mode: models are optional (mocked)")
        else:
            # ensure all models are present in production
            assert self.stt_en and self.stt_vi, "STT models missing"
            assert self.nmt_en_vi and self.nmt_vi_en, "NMT models missing"
            assert self.tts_en and self.tts_vi, "TTS models missing"
            assert self.nlp_en and self.nlp_vi and self.skeleton, "NLP/Skeleton missing"
            print("[PIPELINE] All models provided")

        print("[PIPELINE] Ready")

    # ------------------------
    # Run loop
    # ------------------------
    def run(self, start_mode: Mode = Mode.VI_EN) -> None:
        self.mode = start_mode
        self.state = State.READY

        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass

        print("[PIPELINE] Device loop started. Mode:", self.mode)

        while True:
            # --- power / battery display (non-critical) ---
            try:
                percent = self.power.get_percent()
            except Exception:
                percent = 100
            try:
                getattr(self.display, "show_battery", lambda p: None)(percent)
            except Exception:
                pass

            # --- auto shutdown on critical battery ---
            try:
                if getattr(self.power, "should_shutdown", None):
                    if self.power.should_shutdown():
                        try:
                            self.display.show_status("Pin yếu — tắt máy")
                        except Exception:
                            pass
                        self.power.shutdown()
                        return
                else:
                    if self.power.is_low():
                        try:
                            self.display.show_status("Pin yếu — tắt máy")
                        except Exception:
                            pass
                        self.power.shutdown()
                        return
            except Exception:
                pass

            # --- mode button handling ---
            try:
                mode_event = self.buttons.poll_mode_event()
                if mode_event == "short":
                    self._toggle_mode()
                elif mode_event == "long":
                    try:
                        self.display.show_status("Tắt thiết bị")
                    except Exception:
                        pass
                    self.power.shutdown()
                    return
            except Exception:
                pass

            # --- talk button press (push-to-talk style) ---
            try:
                if self.buttons.is_talk_pressed():
                    self._handle_talk()
            except Exception:
                pass

            time.sleep(0.05)

    # ------------------------
    # Helpers
    # ------------------------
    def _toggle_mode(self) -> None:
        self.mode = Mode.EN_VI if self.mode == Mode.VI_EN else Mode.VI_EN
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass
        print("[MODE] Switched to", self.mode)

    # ------------------------
    # Talk flow
    # ------------------------
    def _handle_talk(self) -> None:
        """
        Full flow:
         - RECORDING
         - STT (language dependent)
         - NLP processing (normalize / fallback)  <-- uses 'ok' flag
         - Skeleton extract -> send skeleton to NMT
         - Compose result with slots
         - TTS
        """

        # --- RECORDING ---
        self.state = State.RECORDING
        try:
            self.display.show_status(
                "Đang nghe...", mode=self.mode, state=self.state.name
            )
        except Exception:
            pass

        try:
            self.audio.start_record()
        except Exception as e:
            print("[AUDIO] start_record failed:", e)
            return

        # wait until release
        try:
            while self.buttons.is_talk_pressed():
                time.sleep(0.02)
        except Exception:
            time.sleep(0.5)

        try:
            wav_path = self.audio.stop_record()
        except Exception as e:
            print("[AUDIO] stop_record failed:", e)
            return

        # --- TRANSLATING ---
        self.state = State.TRANSLATING
        try:
            self.display.show_status(
                "Đang dịch...", mode=self.mode, state=self.state.name
            )
        except Exception:
            pass

        # DEV mode shortcut
        if self.device_env == "DEV":
            text_out = "[DEV] Translation result"
            print("[PIPELINE][DEV] pretending translation ->", text_out)
        else:
            # 1) STT -> text_in
            try:
                if self.mode == Mode.VI_EN:
                    text_in = self.stt_vi.transcribe(wav_path)
                else:
                    text_in = self.stt_en.transcribe(wav_path)
            except Exception as e:
                print("[STT] error:", e)
                text_in = ""

            # 2) NLP process: normalization / fallback
            try:
                nlp_proc = self.nlp_vi if self.mode == Mode.VI_EN else self.nlp_en
                nlp_result = nlp_proc.process(text_in)
            except Exception as e:
                print("[NLP] error:", e)
                nlp_result = {
                    "ok": False,
                    "text": "",
                    "fallback": "Mình không nghe rõ, bạn nói lại nhé.",
                }

            # ==== KEY CHANGE: check 'ok' per your NLP interface ====
            if not nlp_result.get("ok", False):
                fallback = nlp_result.get("fallback", "") or (
                    "Please say again"
                    if self.mode == Mode.EN_VI
                    else "Bạn nói lại giúp mình"
                )
                try:
                    # speak fallback with appropriate TTS
                    if self.mode == Mode.VI_EN:
                        self.tts_vi.speak(fallback)
                    else:
                        self.tts_en.speak(fallback)
                except Exception as e:
                    print("[TTS] fallback speak failed:", e)
                # back to ready
                self.state = State.READY
                try:
                    self.display.show_mode(self.mode)
                except Exception:
                    pass
                return

            # 3) Skeleton extraction (extract skeleton + slots)
            try:
                if self.mode == Mode.VI_EN:
                    skel, slots = self.skeleton.extract_vi(nlp_result["text"])
                else:
                    skel, slots = self.skeleton.extract_en(nlp_result["text"])
            except Exception as e:
                print("[SKELETON] extract error:", e)
                skel, slots = nlp_result.get("text", ""), {}

            # 4) NMT translate on skeleton only
            try:
                if self.mode == Mode.VI_EN:
                    translated_raw = self.nmt_vi_en.translate(skel)
                else:
                    translated_raw = self.nmt_en_vi.translate(skel)
            except Exception as e:
                print("[NMT] translate error:", e)
                translated_raw = ""

            # 5) Compose translated skeleton + slots
            try:
                out = self.skeleton.compose(translated_raw, slots)
            except Exception as e:
                print("[SKELETON] compose error:", e)
                out = translated_raw or nlp_result.get("text", "")

            text_out = out

        # --- SPEAKING ---
        self.state = State.SPEAKING
        try:
            self.display.show_status(
                "Đang phát...", mode=self.mode, state=self.state.name
            )
        except Exception:
            pass

        if self.device_env != "DEV":
            try:
                if self.mode == Mode.VI_EN:
                    self.tts_en.speak(text_out)
                else:
                    self.tts_vi.speak(text_out)
            except Exception as e:
                print("[TTS] speak error:", e)

        # back to ready
        self.state = State.READY
        try:
            self.display.show_mode(self.mode)
        except Exception:
            pass
