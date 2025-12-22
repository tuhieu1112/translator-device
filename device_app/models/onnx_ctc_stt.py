from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
import soundfile as sf
from transformers import Wav2Vec2Processor


@dataclass
class OnnxCTCSTT:
    """
    Backend STT dùng model ONNX CTC + Wav2Vec2Processor
    (FIXED VERSION – SAFE FOR RUNTIME)
    """

    model_path: Path
    processor_dir: Path
    lang: str = "vi"

    def __post_init__(self) -> None:
        self.model_path = Path(self.model_path)
        self.processor_dir = Path(self.processor_dir)

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

        self.processor = Wav2Vec2Processor.from_pretrained(str(self.processor_dir))

    # --------------------------------------------------
    # MAIN API
    # --------------------------------------------------
    def transcribe_file(self, wav_path: str | Path) -> str:
        wav_path = str(wav_path)

        # 1️⃣ Load audio
        audio, sr = sf.read(wav_path)

        # 2️⃣ Check sample rate (BẮT BUỘC)
        if sr != 16000:
            raise ValueError(f"Invalid sample rate {sr}, wav2vec2 requires 16000 Hz")

        # 3️⃣ Convert to mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # 4️⃣ Audio quá ngắn → bỏ qua
        if audio.shape[0] < 400:  # ~25ms
            return ""

        # 5️⃣ float32
        audio = audio.astype(np.float32)

        # 6️⃣ Add batch dim (QUAN TRỌNG NHẤT)
        audio = np.expand_dims(audio, axis=0)
        # shape: (1, num_samples)

        # 7️⃣ Processor
        inputs = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="np",
            padding=True,
        )

        # DEBUG – bạn có thể bỏ sau khi ổn
        # print("STT input_values shape:", inputs["input_values"].shape)

        # 8️⃣ ONNX inference
        logits = self.session.run(None, {"input_values": inputs["input_values"]})[0]

        # 9️⃣ Decode CTC
        pred_ids = np.argmax(logits, axis=-1)
        text = self.processor.batch_decode(pred_ids)[0]

        return text.strip()
