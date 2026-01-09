from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

import numpy as np
import sounddevice as sd
import soundfile as sf
import librosa


# ================= DEFAULT CONFIG =================

DEFAULT_INPUT_DEVICE = 1
DEFAULT_OUTPUT_DEVICE = 1

STT_SAMPLE_RATE = 16000
TTS_SAMPLE_RATE = 44100
MIN_RECORD_SEC = 1  # chống bấm nhầm


class AudioBackend:
    """
    Audio backend cho thiết bị dịch

    - Push-to-talk recording
    - Resample về 16kHz cho STT
    - Playback cho TTS
    """

    def __init__(self, config: Dict[str, Any]):
        audio_cfg = config.get("AUDIO", {})

        self.input_device = int(audio_cfg.get("INPUT_DEVICE", DEFAULT_INPUT_DEVICE))
        self.output_device = int(audio_cfg.get("OUTPUT_DEVICE", DEFAULT_OUTPUT_DEVICE))
        self.channels = int(audio_cfg.get("CHANNELS", 1))

        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._orig_sr: int | None = None

        base = Path(config.get("ARTIFACTS_DIR", "artifacts"))
        tmp = base / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        self._wav_path = tmp / "ptt_record.wav"

        print(
            "[AUDIO] Init | "
            f"IN_DEV={self.input_device} | OUT_DEV={self.output_device} | "
            f"STT_SR={STT_SAMPLE_RATE} | TTS_SR={TTS_SAMPLE_RATE}"
        )

    # ================= RECORD =================

    def start_record(self) -> None:
        self._frames = []

        def callback(indata, frames, time_info, status):
            if status:
                print("[AUDIO][WARN]", status)
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            device=self.input_device,
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

        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        duration = len(audio) / float(self._orig_sr or 1)
        if duration < MIN_RECORD_SEC:
            raise RuntimeError("Recording too short")

        audio_16k = librosa.resample(
            audio,
            orig_sr=self._orig_sr,
            target_sr=STT_SAMPLE_RATE,
        )

        sf.write(self._wav_path, audio_16k, STT_SAMPLE_RATE)
        print(f"[AUDIO] Saved STT wav @16kHz: {self._wav_path}")

        return self._wav_path

    # ================= PLAYBACK (TTS) =================

    def play(self, audio: np.ndarray) -> None:
        sd.play(
            audio,
            samplerate=TTS_SAMPLE_RATE,
            device=self.output_device,
        )
        sd.wait()

    # ================= PIPELINE COMPAT =================

    def speak(self, audio: np.ndarray) -> None:
        """
        Alias để tương thích pipeline:
        pipeline gọi self.audio.speak(...)
        """
        self.play(audio)


# ================= FACTORY =================


def create_audio(config: Dict[str, Any]):
    print("[AUDIO] Using AudioBackend")
    return AudioBackend(config)
