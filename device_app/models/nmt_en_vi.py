from dataclasses import dataclass, field
from typing import Any
from device_app.models.nmt_base import NMTBase


@dataclass
class NMTEnVi:
    config: Any
    _impl: NMTBase = field(init=False)

    def __post_init__(self) -> None:
        # OPUS-MT / Marian: EN -> VI
        self._impl = NMTBase(model_dir="artifacts/nmt_en_vi")

    def translate(self, text: str) -> str:
        return self._impl.translate(text)
