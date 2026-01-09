from __future__ import annotations

import time
import tempfile
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly


class AudioBackend:
    """
    SAFE Audio backend for Raspberry Pi + USB soundcard

    Design:
    - Record at hardware sample rate (usually 44100 / 48000)
    - Resample to STT sample rate (16k)
    - No librosa
    - No numba
    - Never crash pipeline
    """

    def __init__(self, cfg: dict):
        audio_cfg = cfg.get("AUDIO", {})

        # STT expects 16k
        self.stt_rate: int = int(audio_cfg.get("STT_RATE", 16000))

        # Hardware rate (USB mic thường là 48000)
        self.hw_rate: int = int(audio_cfg.get("SAMPLE_RATE", 48000))

        self.channels: int = int(audio_cfg.get("CHANNELS", 1))
        self.max_seconds: int = int(audio_cfg.get("MAX_RECORD_SECONDS", 10))

        self.input_device = audio_cfg.get("INPUT_DEVICE", None)
        self.output_device = audio_cfg.get("OUTPUT_DEVICE", None)

        self._buffer: Optional[np.ndarray] = None
        self._record_t0: Optional[float] = None

        print(
            f"[AUDIO] Init | HW_SR={self.hw_rate} | STT_SR={self.stt_rate} | "
            f"CH={self.channels} | IN_DEV={self.input_device} | OUT_DEV={self.output_device}"
        )

    # ==================================================
    # RECORD
    # ==================================================

    def start_record(self) -> None:
        """Start recording (non-blocking)."""
        self._record_t0 = time.monotonic()
        self._buffer = None

        try:
            self._buffer = sd.rec(
                int(self.max_seconds * self.hw_rate),
                samplerate=self.hw_rate,
                channels=self.channels,
                dtype="int16",
                device=self.input_device,
            )
            print("[AUDIO] Recording started")
        except Exception as e:
            self._buffer = None
            raise RuntimeError(f"start_record failed: {e}")

    def stop_record(self) -> str:
        """
        Stop recording.
        Returns path to 16kHz WAV file for STT.
        """
        try:
            sd.wait()
        except Exception:
            pass

        if self._buffer is None:
            raise RuntimeError("stop_record: no buffer")

        duration = time.monotonic() - (self._record_t0 or time.monotonic())

        # quá ngắn → bỏ
        if duration < 0.3:
            print("[AUDIO] stop_record: too short")
            raise RuntimeError("recording too short")

        audio = np.asarray(self._buffer).squeeze()

        if audio.size == 0:
            raise RuntimeError("stop_record: no frames")

        # ---- resample về 16k cho STT ----
        if self.hw_rate != self.stt_rate:
            audio = resample_poly(audio, self.stt_rate, self.hw_rate)

        # ---- save temp wav ----
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="rec_", dir="/tmp"
        )
        sf.write(tmp.name, audio, self.stt_rate)
        tmp.close()

        print(f"[AUDIO] Saved: {tmp.name}")
        return tmp.name

    # ==================================================
    # PLAY
    # ==================================================

    def play_wav(self, wav_path: str) -> None:
        """Play wav file safely."""
        try:
            audio, sr = sf.read(wav_path, dtype="int16")
            sd.play(audio, sr, device=self.output_device)
            sd.wait()
        except Exception as e:
            print("[AUDIO] play failed:", e)


# ================= FACTORY =================


class DebugAudio:
    def start_record(self):
        print("[AUDIO][DEBUG] start_record")

    def stop_record(self) -> str:
        raise RuntimeError("DEBUG audio: no recording")

    def play_wav(self, wav_path: str):
        print("[AUDIO][DEBUG] play", wav_path)


def create_audio(cfg: dict):
    mode = str(cfg.get("AUDIO_MODE", "alsa")).lower()
    if mode == "alsa":
        print("[AUDIO] Using ALSA / sounddevice backend")
        return AudioBackend(cfg)
    print("[AUDIO] Using DEBUG backend")
    return DebugAudio()
