from dataclasses import dataclass, field
from typing import Any
from device_app.models.nmt_base import NMTBase


@dataclass
class NMTViEn:
    config: Any
    _impl: NMTBase = field(init=False)

    def __post_init__(self) -> None:
        # OPUS-MT / Marian: VI -> EN (hướng đã cố định trong model)
        self._impl = NMTBase(model_dir="artifacts/nmt_vi_en")

    def translate(self, text: str) -> str:
        return self._impl.translate(text)
