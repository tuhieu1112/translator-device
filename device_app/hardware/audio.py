from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa


class DebugAudio:
    def __init__(self, config: Dict[str, Any]):
        audio_cfg = config.get("AUDIO", {})
        self.target_sr = int(audio_cfg.get("SAMPLE_RATE", 16000))
        self.channels = int(audio_cfg.get("CHANNELS", 1))

        self._frames = []
        self._stream = None

        base = Path(config.get("ARTIFACTS_DIR", "artifacts"))
        tmp = base / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        self._wav_path = tmp / "ptt_record.wav"

        print(f"[AUDIO] Target SR={self.target_sr}")

    def start_record(self):
        self._frames = []

        def callback(indata, frames, time_info, status):
            self._frames.append(indata.copy())

        # ❗ KHÔNG ÉP sample_rate
        self._stream = sd.InputStream(
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()
        print("[AUDIO] Recording started")

    def stop_record(self) -> Path:
        self._stream.stop()
        self._stream.close()
        self._stream = None

        audio = np.concatenate(self._frames, axis=0)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # 🔥 RESAMPLE VỀ 16K
        audio_16k = librosa.resample(
            audio,
            orig_sr=sd.query_devices(None, "input")["default_samplerate"],
            target_sr=self.target_sr,
        )

        sf.write(self._wav_path, audio_16k, self.target_sr)
        print(f"[AUDIO] Saved 16k WAV: {self._wav_path}")
        return self._wav_path


def create_audio(config: Dict[str, Any]):
    print("[AUDIO] Using backend: DebugAudio")
    return DebugAudio(config)
