# device_app/hardware/display.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Display:
    """
    Không hiển thị pin nữa.

    show_status vẫn nhận battery để tương thích với pipeline cũ,
    nhưng sẽ ignore battery.
    """

    mode: str = "debug"

    def __init__(self, config: dict[str, Any]) -> None:
        self.mode = str(config.get("DISPLAY_MODE", "debug")).lower()

    def _print_debug(self, text: str) -> None:
        print(f"[OLED DEBUG] {text}")

    def show_status(
        self,
        text: str = "",
        battery: int | float = 100,  # nhận nhưng ignore
        mode: Any | None = None,
        state: str | None = None,
        **kwargs,
    ) -> None:
        parts: list[str] = []

        if mode is not None:
            mode_name = getattr(mode, "name", str(mode))
            parts.append(f"Mode={mode_name}")

        if state is not None:
            parts.append(f"State={state}")

        if text:
            parts.append(text)

        line = " | ".join(parts) if parts else text

        if self.mode == "debug":
            self._print_debug(line)
        else:
            # TODO: OLED thật (SSD1306) sau
            self._print_debug(line)

    def show_mode(self, mode: Any, battery: int | float = 100) -> None:
        mode_name = getattr(mode, "name", str(mode))
        self.show_status(text=f"Mode={mode_name}", mode=mode, state="IDLE")


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
