from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Display:
    """
    Display backend (debug / OLED-ready)

    Hiển thị:
    - Chế độ dịch (VI → EN / EN → VI)
    - Trạng thái thiết bị (READY / Listening / Translating / Speaking)
    - Mức pin (%)

    Khi chưa gắn OLED / ADS:
    - Chạy ở chế độ debug
    - In trạng thái ra terminal
    """

    mode: str = "debug"

    def __init__(self, config: dict[str, Any]) -> None:
        self.mode = str(config.get("DISPLAY_MODE", "debug")).lower()

    # ================= INTERNAL =================

    def _print_debug(self, lines: list[str]) -> None:
        print("[OLED]")
        for line in lines:
            print(line)

    def _map_state(self, state: str | None) -> str:
        """
        Map internal pipeline state to user-friendly text
        """
        if state is None:
            return ""

        state = state.upper()
        return {
            "IDLE": "READY",  # tương thích pipeline cũ
            "READY": "READY",
            "RECORDING": "Listening...",
            "TRANSLATING": "Translating...",
            "SPEAKING": "Speaking...",
        }.get(state, state)

    # ================= PUBLIC API =================

    def show_status(
        self,
        text: str = "",
        battery: int | float | None = None,
        mode: Any | None = None,
        state: str | None = None,
        **kwargs,
    ) -> None:
        lines: list[str] = []

        # ----- LINE 1: MODE + BATTERY -----
        if mode is not None:
            mode_name = getattr(mode, "name", str(mode))
            header = f"MODE: {mode_name.replace('_', ' → ')}"
        else:
            header = "MODE: ?"

        if battery is not None:
            header = f"{header:<18} BAT: {int(battery)}%"

        lines.append(header)

        # ----- LINE 2: STATUS -----
        status_text = self._map_state(state)
        if status_text:
            lines.append(f"STATUS: {status_text}")
        else:
            lines.append("")

        # ----- LINE 3: TEXT / HINT -----
        lines.append(text if text else "")

        # ----- OUTPUT -----
        if self.mode == "debug":
            self._print_debug(lines)
        else:
            # TODO: OLED SSD1306 implementation
            self._print_debug(lines)

    def show_mode(self, mode: Any, battery: int | float | None = None) -> None:
        """
        Hiển thị trạng thái sẵn sàng ban đầu
        """
        self.show_status(
            text="Press TALK to speak",
            battery=battery,
            mode=mode,
            state="READY",
        )

    def show_battery(self, percent: int | float) -> None:
        """
        Stub để tương thích pipeline khi chưa gắn OLED / ADS
        """
        if self.mode == "debug":
            print(f"[OLED DEBUG] Battery: {int(percent)}%")


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
