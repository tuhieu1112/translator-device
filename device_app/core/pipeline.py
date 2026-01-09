from __future__ import annotations

import time
import soundfile as sf
import numpy as np
from scipy.signal import resample_poly
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
    # TALK BUTTON
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

            # -------- LOAD + NORMALIZE AUDIO FOR STT --------
            audio, sr = sf.read(wav_path, dtype="float32")

            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            if sr != 16000:
                audio = resample_poly(audio, 16000, sr)
                sr = 16000

            stt_wav = wav_path.replace(".wav", "_stt.wav")
            sf.write(stt_wav, audio, sr)

            # -------- STT --------
            if self.mode == Mode.VI_EN:
                text_in = self.stt_vi.transcribe_file(stt_wav)
            else:
                text_in = self.stt_en.transcribe_file(stt_wav)

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
                skel, slots = self.skeleton.extract_vi(result["text"])
                translated = self.nmt_vi_en.translate(skel)
                text_out = self.skeleton.compose(translated, slots)
                self._tts_play(self.tts_en, text_out)
            else:
                skel, slots = self.skeleton.extract_en(result["text"])
                translated = self.nmt_en_vi.translate(skel)
                text_out = self.skeleton.compose(translated, slots)
                self._tts_play(self.tts_vi, text_out)

        except Exception as e:
            print("[PIPELINE] talk flow error:", e)

        self._back_to_ready()

    # ==================================================
    # TTS SAFE PLAY
    # ==================================================

    def _tts_play(self, tts, text: str) -> None:
        wav_path = tts.synthesize_to_file(text)

        audio, sr = sf.read(wav_path, dtype="float32")
        if sr != 48000:
            audio = resample_poly(audio, 48000, sr)
            sr = 48000

        self.audio.play_array(audio, sr)

    # ==================================================
    # FALLBACK
    # ==================================================

    def _speak_fallback(self, text: str) -> None:
        try:
            if self.mode == Mode.VI_EN:
                self._tts_play(self.tts_vi, text)
            else:
                self._tts_play(self.tts_en, text)
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
