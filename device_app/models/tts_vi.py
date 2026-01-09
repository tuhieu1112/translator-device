from __future__ import annotations

import os
import tempfile
from typing import Optional

from device_app.models.tts_base import TTSBase
from device_app.models.piper_tts import PiperTTS


class TTSVi(TTSBase):
    """
    Vietnamese TTS
    - Backend: Piper
    - Input: text (str)
    - Output: play audio via Audio backend (48k)
    """

    def __init__(
        self,
        *,
        audio,
        model_path: str,
        speaker: Optional[int] = None,
        speed: float = 1.0,
    ) -> None:
        """
        audio      : Audio backend (hardware/audio.py)
        model_path : path to piper .onnx model
        speaker    : speaker id (if multi-speaker model)
        speed      : speaking speed
        """
        self.audio = audio

        self._engine = PiperTTS(
            model_path=model_path,
            speaker=speaker,
            speed=speed,
        )

        print("[TTS_VI] Initialized (Piper)")

    # ==================================================
    # PUBLIC API (USED BY PIPELINE)
    # ==================================================

    def speak(self, text: str) -> None:
        """
        Pipeline-safe speak()
        - Generate WAV
        - Resample to HW SR
        - Play via audio backend
        """
        if not text or not text.strip():
            print("[TTS_VI] Empty text → skip")
            return

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        try:
            self._engine.synthesize_to_file(
                text=text,
                wav_path=wav_path,
            )

            self.audio.play_wav(wav_path)

        except Exception as e:
            print("[TTS_VI] speak failed:", e)

        finally:
            try:
                os.remove(wav_path)
            except Exception:
                pass

    # ==================================================
    # OPTIONAL: used for debug / offline
    # ==================================================

    def synthesize_to_file(self, text: str, wav_path: str) -> None:
        """
        Generate WAV only (no playback)
        """
        self._engine.synthesize_to_file(
            text=text,
            wav_path=wav_path,
        )
