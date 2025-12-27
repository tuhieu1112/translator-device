from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import os

import numpy as np
import sounddevice as sd
import soundfile as sf


class DebugAudio:
    def __init__(self, config: Dict[str, Any]):
        audio_cfg = config.get("AUDIO", {})
        self.sample_rate = int(audio_cfg.get("SAMPLE_RATE", 16000))
        self.channels = int(audio_cfg.get("CHANNELS", 1))

        self._frames = []
        self._stream = None

        # ✅ FIX WINDOWS + LINUX
        self._wav_path = Path(os.environ.get("TMP", "/tmp")) / "ptt_record.wav"

        print(f"[AUDIO] DebugAudio ready (sr={self.sample_rate})")

    def record(self) -> Path:
        self.start_record()
        input("[AUDIO] Press Enter to stop recording...")
        return self.stop_record()

    def start_record(self):
        self._frames = []

        def callback(indata, frames, time_info, status):
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=callback,
        )
        self._stream.start()
        print("[AUDIO] Recording started")

    def stop_record(self) -> Path:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        audio = np.concatenate(self._frames, axis=0)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        sf.write(self._wav_path, audio, self.sample_rate)
        print(f"[AUDIO] Recording saved: {self._wav_path}")
        return self._wav_path


def create_audio(config: Dict[str, Any]):
    print("[AUDIO] Using backend: DebugAudio")
    return DebugAudio(config)
