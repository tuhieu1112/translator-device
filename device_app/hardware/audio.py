# device_app/hardware/audio.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import time
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf


# ----------------- Base class -----------------


class AudioBackend:
    """Interface chung cho backend audio."""

    def record(self, hold_to_stop: bool = False) -> Path:
        """
        Thu âm và trả về đường dẫn file WAV.
        - hold_to_stop: để dành cho backend trên Raspberry Pi
          (nhấn giữ để thu, thả ra để dừng). Trên laptop debug
          sẽ giả lập bằng Enter để DỪNG.
        """
        raise NotImplementedError

    def play(self, wav_path: Path) -> None:
        """Phát file WAV."""
        raise NotImplementedError


# ----------------- Debug backend (laptop mic) -----------------


@dataclass
class DebugAudio(AudioBackend):
    """
    Backend dùng mic + loa của laptop.
    - Ghi âm bằng sounddevice
    - Lưu vào artifacts/debug_audio

    Trên laptop (debug):

      * Ở màn hình [MAIN] bạn nhấn Enter để bắt đầu 1 lượt pipeline.
      * Trong hàm record():
          - VỪA GỌI record() LÀ BẮT ĐẦU GHI NGAY
          - Nhấn Enter một lần nữa để DỪNG ghi
          - Nếu không bấm thì tự dừng sau tối đa 10s
    """

    config: Dict[str, Any]

    def __post_init__(self) -> None:
        audio_cfg = self.config.get("AUDIO", {})
        self.sample_rate: int = int(audio_cfg.get("SAMPLE_RATE", 16000))
        self.channels: int = int(audio_cfg.get("CHANNELS", 1))
        self.max_seconds: int = int(audio_cfg.get("MAX_RECORD_SECONDS", 15))

        # Thư mục lưu debug wav
        artifacts_dir = Path(self.config.get("ARTIFACTS_DIR", "artifacts"))
        self.debug_dir = artifacts_dir / "debug_audio"
        self.debug_dir.mkdir(parents=True, exist_ok=True)

        print(
            f"[AUDIO] DebugAudio initialized "
            f"(sr={self.sample_rate}, ch={self.channels}, "
            f"max={self.max_seconds}s, dir={self.debug_dir})"
        )

    # -------- recording --------

    def record(self, hold_to_stop: bool = False) -> Path:
        """
        Ghi âm từ mic laptop.

        Luồng debug trên PC:
        - Bạn đã nhấn Enter ở [MAIN] → pipeline.run_once() được gọi → record() chạy.
        - record() BẮT ĐẦU GHI NGAY LẬP TỨC.
        - Nhấn Enter thêm một lần nữa để DỪNG.
        - Nếu không nhấn → tự dừng sau min(MAX_RECORD_SECONDS, 10) giây.
        """
        ts = int(time.time())
        wav_path = self.debug_dir / f"input_{ts}.wav"

        # Giới hạn tối đa 10s cho debug
        duration = min(self.max_seconds, 10)

        print(
            f"[AUDIO DEBUG] BẮT ĐẦU ghi (tối đa {duration} s @ {self.sample_rate} Hz)..."
        )
        print(
            "[AUDIO DEBUG] Nhấn Enter để DỪNG ghi (hoặc tự dừng sau giới hạn thời gian)."
        )

        # Cờ dừng ghi (dùng dict để mutable trong closure)
        stop_flag = {"stop": False}

        # Thread chờ Enter để dừng
        def wait_for_stop():
            input()
            stop_flag["stop"] = True

        stop_thread = threading.Thread(target=wait_for_stop, daemon=True)
        stop_thread.start()

        frames = []

        def callback(indata, frames_count, time_info, status):
            # Lưu frame hiện tại
            frames.append(indata.copy())
            # Nếu đã bấm Enter hoặc hết thời gian thì dừng stream
            if stop_flag["stop"]:
                raise sd.CallbackStop()

        # Mở stream thu âm
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=callback,
        ):
            start = time.time()
            # Vòng lặp chờ cho đến khi nhấn Enter hoặc hết thời gian
            while not stop_flag["stop"]:
                if time.time() - start >= duration:
                    stop_flag["stop"] = True
                    break
                time.sleep(0.05)

        # Ghép các frame lại
        if frames:
            data = np.concatenate(frames, axis=0)
        else:
            # Trường hợp dừng quá nhanh
            data = np.zeros((1, self.channels), dtype="float32")

        # Nếu nhiều kênh → chuyển về mono
        if data.ndim > 1:
            data = data.mean(axis=1)

        sf.write(str(wav_path), data, self.sample_rate)
        print(f"[AUDIO DEBUG] Saved WAV to {wav_path}")

        return wav_path

    # -------- playback --------

    def play(self, wav_path: Path) -> None:
        wav_path = Path(wav_path)
        if not wav_path.is_file():
            print(f"[AUDIO DEBUG] File không tồn tại: {wav_path}")
            return

        data, sr = sf.read(str(wav_path), dtype="float32")
        # Nếu stereo → mono
        if data.ndim > 1:
            data = data.mean(axis=1)

        print(
            f"[AUDIO DEBUG] Phát âm thanh (sr={sr}, samples={data.shape[0]}) "
            f"từ {wav_path}..."
        )
        sd.play(data, sr)
        sd.wait()


# ----------------- Factory -----------------


def create_audio(config: Dict[str, Any]) -> AudioBackend:
    """
    Factory tạo backend audio dựa theo config.AUDIO_MODE.
    Hiện tại:
      - 'debug' hoặc bất kỳ giá trị nào khác → DebugAudio (mic laptop).
    Sau này khi lên Raspberry Pi bạn có thể thêm:
      - if mode == "pi": return Es8388Audio(...)
    """
    mode = str(config.get("AUDIO_MODE", "debug")).lower()

    if mode == "debug":
        print("[AUDIO] Using backend: DebugAudio")
        return DebugAudio(config)

    # Fallback: dùng DebugAudio nếu mode chưa được hỗ trợ
    print(f"[AUDIO] AUDIO_MODE='{mode}' chưa được hỗ trợ, dùng DebugAudio.")
    return DebugAudio(config)
