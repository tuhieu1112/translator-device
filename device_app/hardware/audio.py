from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa


# ================= CONFIG CỨNG (ỔN ĐỊNH TRÊN PI) =================

INPUT_DEVICE = 1  # USB Audio Device (mic)
OUTPUT_DEVICE = 1  # USB Audio Device (loa)

STT_SAMPLE_RATE = 16000
TTS_SAMPLE_RATE = 44100


class DebugAudio:
    def __init__(self, config: Dict[str, Any]):
        audio_cfg = config.get("AUDIO", {})
        self.channels = int(audio_cfg.get("CHANNELS", 1))

        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._orig_sr: int | None = None

        base = Path(config.get("ARTIFACTS_DIR", "artifacts"))
        tmp = base / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        self._wav_path = tmp / "ptt_record.wav"

        print(
            f"[AUDIO] Init | INPUT_DEVICE={INPUT_DEVICE} "
            f"| STT_SR={STT_SAMPLE_RATE} | TTS_SR={TTS_SAMPLE_RATE}"
        )

    # ================= PUSH TO TALK =================

    def start_record(self):
        self._frames = []

        def callback(indata, frames, time_info, status):
            if status:
                print("[AUDIO][WARN]", status)
            self._frames.append(indata.copy())

        # ⚠️ KHÔNG set samplerate → để mic chạy native SR
        self._stream = sd.InputStream(
            device=INPUT_DEVICE,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        )

        self._orig_sr = int(self._stream.samplerate)
        self._stream.start()

        print(f"[AUDIO] Recording started (native_sr={self._orig_sr})")

    def stop_record(self) -> Path:
        if not self._stream:
            raise RuntimeError("Audio stream not started")

        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._frames:
            raise RuntimeError("No audio captured")

        audio = np.concatenate(self._frames, axis=0)

        # mono hóa nếu cần
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # 🔥 RESAMPLE VỀ 16K CHO STT
        audio_16k = librosa.resample(
            audio,
            orig_sr=self._orig_sr,
            target_sr=STT_SAMPLE_RATE,
        )

        sf.write(self._wav_path, audio_16k, STT_SAMPLE_RATE)
        print(f"[AUDIO] Saved STT wav @16kHz: {self._wav_path}")

        return self._wav_path

    # ================= PLAY (TTS) =================

    def play(self, audio: np.ndarray):
        sd.play(
            audio,
            samplerate=TTS_SAMPLE_RATE,
            device=OUTPUT_DEVICE,
        )
        sd.wait()


def create_audio(config: Dict[str, Any]):
    print("[AUDIO] Using backend: DebugAudio (fixed)")
    return DebugAudio(config)
