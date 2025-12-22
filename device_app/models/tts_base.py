# device_app/models/tts_base.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional
import subprocess
import tempfile

import soundfile as sf
import sounddevice as sd


@dataclass
class TTSBase:
    """
    Base class chung cho TTS EN / VI.

    - Đọc cấu hình từ config["TTS"][...]
    - Nếu BACKEND = "piper": gọi piper để sinh WAV rồi phát luôn.
    - Nếu BACKEND = "debug": chỉ in chữ (phòng khi piper lỗi).
    """

    lang: str
    backend: str = "debug"
    piper_exe: Optional[Path] = None
    voice_path: Optional[Path] = None

    def __init__(self, config: Mapping[str, Any], tts_key: str, lang: str) -> None:
        """
        tts_key: "EN" hoặc "VI" (key con trong TTS: ...)
        lang  : mã hiển thị (en/vi) để log cho dễ nhìn.
        """
        self.lang = lang

        tts_cfg = config.get("TTS", {}).get(tts_key, {}) or {}
        self.backend = str(tts_cfg.get("BACKEND", "debug")).lower()

        exe = tts_cfg.get("PIPER_EXE")
        self.piper_exe = Path(exe) if exe else None

        voice = tts_cfg.get("VOICE")
        self.voice_path = Path(voice) if voice else None

    # -------------------------------------------------
    # Hàm public dùng trong pipeline
    # -------------------------------------------------
    def speak(self, text: str) -> None:
        """
        Đọc (hoặc giả lập đọc) câu 'text'.
        """
        text = (text or "").strip()
        if not text:
            return

        if self.backend == "piper":
            try:
                self._speak_with_piper(text)
                return
            except Exception as e:  # nếu Piper lỗi thì fallback debug
                print(f"[TTS {self.lang}] Piper lỗi: {e!r} -> fallback DEBUG")

        # Fallback: chỉ in chữ
        print(f"[TTS DEBUG {self.lang}] {text}")

    # -------------------------------------------------
    # Nội bộ: dùng Piper
    # -------------------------------------------------
    def _speak_with_piper(self, text: str) -> None:
        if not self.piper_exe or not self.voice_path:
            raise RuntimeError("Piper chưa cấu hình đúng PIPER_EXE / VOICE")

        if not self.piper_exe.is_file():
            raise FileNotFoundError(f"Không tìm thấy piper: {self.piper_exe}")

        # PATH model có thể là tương đối, nên chuẩn hóa về tuyệt đối
        voice_path = self.voice_path
        if not voice_path.is_absolute():
            voice_path = Path.cwd() / voice_path

        if not voice_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy model Piper: {voice_path}")

        # Tạo file WAV tạm
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = Path(f.name)

        # Một số bản build Piper dùng -m / -f, một số dùng --model / --output_file.
        # Mình ưu tiên dùng dạng dài --model / --output_file (thông dụng hơn).
        cmd = [
            str(self.piper_exe),
            "--model",
            str(voice_path),
            "--output_file",
            str(wav_path),
        ]

        print(f"[TTS {self.lang}] Piper synthesize...")
        # Piper đọc text từ stdin (UTF-8)
        completed = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"Piper trả về mã lỗi {completed.returncode}, "
                f"stderr: {completed.stderr.decode(errors='ignore')}"
            )

        # Đọc WAV và phát
        data, sr = sf.read(wav_path, dtype="float32")
        print(f"[TTS {self.lang}] Phát âm thanh (sr={sr}, {len(data)} mẫu)...")
        sd.play(data, sr)
        sd.wait()
