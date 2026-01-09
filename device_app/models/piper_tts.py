# piper_tts.py
from __future__ import annotations
import shutil
import subprocess
import sys
import os
from typing import Optional
from tts_base import TTSBase


class PiperTTS(TTSBase):
    """
    TTS implementation that tries to use the `piper` CLI.
    Fallback to pyttsx3 if `piper` is not available.
    """

    def __init__(
        self,
        *,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        piper_exe: str = "piper",
        hw_sr: int = 48000,
        out_device: Optional[int] = None,
    ) -> None:
        super().__init__(hw_sr=hw_sr, out_device=out_device)
        self.model = model
        self.voice = voice
        self.piper_exe = piper_exe
        self._have_piper = shutil.which(self.piper_exe) is not None

        if not self._have_piper:
            try:
                import pyttsx3  # type: ignore

                self._pyttsx3 = pyttsx3
            except Exception:
                self._pyttsx3 = None

    def synthesize_to_file(self, path: str, text: str) -> None:
        if self._have_piper:
            self._synthesize_with_piper(path, text)
            return

        # fallback
        if self._pyttsx3 is not None:
            self._synthesize_with_pyttsx3(path, text)
            return

        raise RuntimeError("No TTS backend available (piper or pyttsx3)")

    def _synthesize_with_piper(self, path: str, text: str) -> None:
        """
        Call: piper -m <model.onnx> -i <input.txt> -f <wav_out>
        NOTE: exact args depend on piper build; we try a safe common invocation.
        """
        # ensure directory exists
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        # create a temporary text file with the text
        import tempfile

        tf = tempfile.NamedTemporaryFile(
            prefix="piper_in_", suffix=".txt", delete=False, mode="w", encoding="utf-8"
        )
        try:
            tf.write(text)
            tf.flush()
            tf.close()
            cmd = [self.piper_exe, "-i", tf.name, "-f", path]

            # if model specified try to add -m
            if self.model:
                cmd.extend(["-m", self.model])

            # voice/other config if needed (piper flag names vary)
            if self.voice:
                # some piper builds accept --speaker or --speaker-id
                cmd.extend(["--speaker", str(self.voice)])

            # run
            completed = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            if completed.returncode != 0:
                # surface error for debugging but try fallback
                print(
                    "[PIPER] synth failed:",
                    completed.returncode,
                    completed.stderr.strip(),
                )
                raise RuntimeError(
                    "piper failed: " + (completed.stderr or completed.stdout)
                )
        finally:
            try:
                os.unlink(tf.name)
            except Exception:
                pass

    def _synthesize_with_pyttsx3(self, path: str, text: str) -> None:
        """
        Very basic fallback: produce WAV using pyttsx3.
        """
        engine = self._pyttsx3.init()
        # pyttsx3 save_to_file is synchronous with runAndWait
        engine.save_to_file(text, path)
        engine.runAndWait()
