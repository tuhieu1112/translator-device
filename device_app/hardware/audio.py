from __future__ import annotations

import time
import wave
import tempfile
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly


class AudioBackend:
    """
    Audio backend SAFE for Raspberry Pi:
    - No librosa
    - No numba
    - No crash if recording too short
    """

    def __init__(self, config: dict[str, Any]) -> None:
        audio_cfg = config.get("AUDIO", {})

        self.sample_rate = int(audio_cfg.get("SAMPLE_RATE", 16000))
        self.channels = int(audio_cfg.get("CHANNELS", 1))
        self.max_seconds = int(audio_cfg.get("MAX_RECORD_SECONDS", 10))

        self.input_device = audio_cfg.get("INPUT_DEVICE", None)
        self.output_device = audio_cfg.get("OUTPUT_DEVICE", None)

        self._recording = False
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

        print(
            f"[AUDIO] Init | SR={self.sample_rate} | CH={self.channels} | "
            f"IN_DEV={self.input_device} | OUT_DEV={self.output_device}"
        )

    # ================= RECORD =================

    def start_record(self) -> None:
        if self._recording:
            return

        self._frames.clear()
        self._recording = True

        def callback(indata, frames, time_info, status):
            if self._recording:
                self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=48000,  # native USB mic SR
            channels=self.channels,
            dtype="int16",
            callback=callback,
            device=self.input_device,
        )

        self._stream.start()
        print("[AUDIO] Recording started")

    def stop_record(self) -> str | None:
        if not self._recording:
            return None

        self._recording = False

        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
        except Exception:
            pass

        if not self._frames:
            print("[AUDIO] stop_record: no frames")
            return None

        audio = np.concatenate(self._frames, axis=0)

        duration = len(audio) / 48000
        if duration < 0.3:
            print("[AUDIO] stop_record: too short")
            return None

        # ---- resample 48k -> 16k (SAFE) ----
        audio_16k = resample_poly(audio, up=1, down=3)

        # ---- write wav ----
        fd, path = tempfile.mkstemp(suffix=".wav")
        with wave.open(path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_16k.tobytes())

        print(f"[AUDIO] Saved: {path}")
        return path

    # ================= PLAY =================

    def play_wav(self, wav_path: str) -> None:
        try:
            with wave.open(wav_path, "rb") as wf:
                data = wf.readframes(wf.getnframes())
                audio = np.frombuffer(data, dtype=np.int16)
                sd.play(audio, wf.getframerate(), device=self.output_device)
                sd.wait()
        except Exception as e:
            print("[AUDIO] play failed:", e)


def create_audio(config: dict[str, Any]) -> AudioBackend:
    return AudioBackend(config)
