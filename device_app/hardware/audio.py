from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly


class create_audio:
    """
    Audio flow chuẩn:
    - Record: 48kHz → downsample 16kHz → STT
    - TTS: Piper 22050Hz → upsample 48kHz → Speaker
    """

    def __init__(
        self,
        *,
        hw_sr: int = 48000,
        stt_sr: int = 16000,
        channels: int = 1,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None,
        tmp_dir: str = "/tmp",
    ) -> None:
        self.hw_sr = int(hw_sr)
        self.stt_sr = int(stt_sr)
        self.channels = int(channels)
        self.input_device = input_device
        self.output_device = output_device
        self.tmp_dir = Path(tmp_dir)

        self._stream: Optional[sd.InputStream] = None
        self._frames: list[np.ndarray] = []

        print(
            f"[AUDIO] Init | HW_SR={self.hw_sr} | STT_SR={self.stt_sr} "
            f"| CH={self.channels} | IN_DEV={self.input_device} | OUT_DEV={self.output_device}"
        )

    # ==================================================
    # RECORD
    # ==================================================

    def start_record(self) -> None:
        if self._stream is not None:
            raise RuntimeError("Recording already started")

        self._frames.clear()

        def callback(indata, frames, time_info, status):
            if status:
                print("[AUDIO] input status:", status)
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.hw_sr,
            channels=self.channels,
            dtype="float32",
            device=self.input_device,
            callback=callback,
        )
        self._stream.start()
        print("[AUDIO] Recording started")

    def stop_record(self) -> str:
        if self._stream is None:
            raise RuntimeError("Recording not started")

        self._stream.stop()
        self._stream.close()
        self._stream = None

        audio = np.concatenate(self._frames, axis=0).squeeze()
        self._frames.clear()

        # ---- Sanity check ----
        if audio.size < self.hw_sr * 0.2:
            raise RuntimeError("Audio too short")

        # ---- Downsample 48k → 16k (STT) ----
        if self.hw_sr != self.stt_sr:
            audio = resample_poly(audio, self.stt_sr, self.hw_sr)

        # ---- Normalize (soft) ----
        peak = np.max(np.abs(audio))
        if peak > 0.99:
            audio = audio / peak * 0.95

        wav_path = self.tmp_dir / f"rec_{uuid.uuid4().hex[:8]}.wav"
        sf.write(wav_path, audio, self.stt_sr, subtype="PCM_16")

        print(f"[AUDIO] Saved: {wav_path}")
        return str(wav_path)

    # ==================================================
    # PLAY (TTS)
    # ==================================================


def play_tts(self, audio: np.ndarray, sr: int) -> None:
    """
    audio: float32 [-1, 1]
    sr: sample rate của Piper (thường 22050)
    """
    if audio.ndim > 1:
        audio = audio.squeeze()

    # ---- Resample → HW SR ----
    if sr != self.hw_sr:
        audio = resample_poly(audio, self.hw_sr, sr)

    # ---- Safety normalize ----
    peak = np.max(np.abs(audio))
    if peak > 0.99:
        audio = audio / peak * 0.95

    sd.play(audio, self.hw_sr, device=self.output_device)
    sd.wait()

    # ==================================================
    # DEBUG / TEST
    # ==================================================

    @staticmethod
    def analyze(audio: np.ndarray, sr: int) -> None:
        rms = np.sqrt(np.mean(audio**2))
        peak = np.max(np.abs(audio))
        clip = np.mean(np.abs(audio) > 0.99)
        dc = float(np.mean(audio))

        print(
            f"[AUDIO STATS] SR={sr} | RMS={rms:.4f} | Peak={peak:.3f} "
            f"| Clip={clip:.4f} | DC={dc:.5f}"
        )
