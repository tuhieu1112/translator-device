# device_app/models/stt_base.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from device_app.models.onnx_ctc_stt import OnnxCTCSTT


class STTBase:
    """
    Base class cho STT EN/VI dùng model ONNX CTC.

    - Nhận config tổng
    - Đọc ra đường dẫn MODEL và PROCESSOR_DIR
    - Tạo backend OnnxCTCSTT
    """

    def __init__(self, config: Mapping[str, Any], lang: str, cfg_key: str) -> None:
        self.lang = lang
        self.cfg_key = cfg_key

        stt_cfg = config.get(cfg_key, {})
        if not stt_cfg:
            raise ValueError(f"Không tìm thấy mục {cfg_key} trong config.yaml")

        # MODEL
        model_rel: Optional[str] = stt_cfg.get("MODEL")
        if not model_rel:
            raise ValueError(f"{cfg_key}.MODEL không được cấu hình trong config.yaml")

        model_path = Path(model_rel)
        if not model_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy STT model: {model_path}")

        # PROCESSOR_DIR
        proc_rel: Optional[str] = stt_cfg.get("PROCESSOR_DIR")
        if not proc_rel:
            raise ValueError(
                f"{cfg_key}.PROCESSOR_DIR không được cấu hình trong config.yaml"
            )

        processor_dir = Path(proc_rel)
        if not processor_dir.is_dir():
            raise FileNotFoundError(
                f"Không tìm thấy thư mục processor: {processor_dir}"
            )

        # Tạo backend ONNX CTC
        self.backend = OnnxCTCSTT(
            model_path=model_path,
            processor_dir=processor_dir,
            lang=lang,
        )

    # ---- API dùng trong pipeline ----
    def transcribe(self, wav_path: str | Path) -> str:
        """Nhận đường dẫn WAV, trả về text."""
        return self.backend.transcribe_file(wav_path)
