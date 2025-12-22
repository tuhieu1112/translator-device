# device_app/models/stt_en.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Union

from .stt_base import STTBase
from .onnx_ctc_stt import OnnxCTCSTT

PathLike = Union[str, Path]


@dataclass
class STTEn(STTBase):
    """
    STT tiếng Anh dùng backend OnnxCTCSTT.

    Trong config.yaml phần STT_EN có thể có 2 kiểu:

    1) Khuyến nghị (rõ ràng nhất):

        STT_EN:
          MODEL_PATH: artifacts/stt_en/stt_en_v1.onnx
          PROCESSOR_DIR: artifacts/stt_en/processor

    2) Kiểu cũ (chỉ có MODEL_DIR), code sẽ tự tìm file .onnx đầu tiên:

        STT_EN:
          MODEL_DIR: artifacts/stt_en
          PROCESSOR_DIR: artifacts/stt_en/processor
    """

    config: Dict[str, Any]

    def __post_init__(self) -> None:
        stt_cfg = self.config.get("STT_EN", {})

        # --- 1. Xác định đường dẫn file model .onnx ---
        model_path_str = stt_cfg.get("MODEL_PATH")

        if model_path_str:
            model_path = Path(model_path_str)
        else:
            # Backward-compat: nếu chỉ có MODEL_DIR thì tự tìm *.onnx trong thư mục
            model_dir_str = stt_cfg.get("MODEL_DIR") or stt_cfg.get("MODEL")
            if not model_dir_str:
                raise ValueError(
                    "Thiếu cấu hình STT_EN.MODEL_PATH hoặc STT_EN.MODEL_DIR "
                    "trong config.yaml."
                )

            model_dir = Path(model_dir_str)
            if not model_dir.is_dir():
                raise ValueError(f"MODEL_DIR '{model_dir}' không phải thư mục hợp lệ.")

            onnx_files = sorted(model_dir.glob("*.onnx"))
            if not onnx_files:
                raise ValueError(
                    f"Không tìm thấy file *.onnx nào trong thư mục '{model_dir}'."
                )

            # Lấy file đầu tiên (nếu có nhiều thì chọn đúng cái mình muốn sau)
            model_path = onnx_files[0]

        if not model_path.is_file():
            raise FileNotFoundError(
                f"File model ONNX không tồn tại hoặc không truy cập được: {model_path}"
            )

        # --- 2. Thư mục processor/tokenizer ---
        processor_dir_str = stt_cfg.get("PROCESSOR_DIR") or stt_cfg.get("PROCESSOR")
        if processor_dir_str:
            processor_dir = Path(processor_dir_str)
        else:
            # Mặc định: cùng thư mục với model, con folder 'processor'
            processor_dir = model_path.parent / "processor"

        # --- 3. Khởi tạo backend OnnxCTCSTT ---
        # LÚC NÀY THAM SỐ ĐẦU TIÊN LÀ FILE .onnx, KHÔNG CÒN LÀ THƯ MỤC NỮA
        self._impl = OnnxCTCSTT(str(model_path), str(processor_dir))

    # ------------------------------------------------------------------
    # API dùng trong pipeline
    # ------------------------------------------------------------------
    def transcribe_file(self, wav_path: PathLike) -> str:
        """
        Nhận đường dẫn file WAV và trả về text tiếng Anh.
        Tự tương thích với nhiều kiểu đặt tên hàm trong backend.
        """
        backend = self._impl
        path = str(wav_path)

        if hasattr(backend, "transcribe_file"):
            return backend.transcribe_file(path)
        if hasattr(backend, "infer_file"):
            return backend.infer_file(path)
        if hasattr(backend, "infer_from_file"):
            return backend.infer_from_file(path)
        if hasattr(backend, "transcribe"):
            return backend.transcribe(path)

        raise AttributeError(
            "Backend OnnxCTCSTT không có hàm nào trong các hàm "
            "[transcribe_file, infer_file, infer_from_file, transcribe]."
        )
