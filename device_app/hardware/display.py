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

    Khi chưa gắn OLED:
    - Chạy debug mode (in terminal)
    """

    mode: str = "debug"

    def __init__(self, config: dict[str, Any]) -> None:
        self.mode = str(config.get("DISPLAY_MODE", "debug")).lower()
        self._last_battery: int | None = None

    # ================= INTERNAL =================

    def _print_debug(self, lines: list[str]) -> None:
        print("[OLED]")
        for line in lines:
            print(line)

    def _map_state(self, state: str | None) -> str:
        if not state:
            return ""

        state = state.upper()
        return {
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
        lines.append(f"STATUS: {status_text}" if status_text else "")

        # ----- LINE 3: TEXT -----
        lines.append(text or "")

        # ----- OUTPUT -----
        if self.mode == "debug":
            self._print_debug(lines)
        else:
            # TODO: SSD1306 OLED backend
            self._print_debug(lines)

    def show_mode(self, mode: Any, battery: int | float | None = None) -> None:
        self.show_status(
            text="Press TALK to speak",
            battery=battery,
            mode=mode,
            state="READY",
        )

    def show_battery(self, percent: int | float) -> None:
        """
        Chỉ dùng cho OLED thật.
        Debug mode KHÔNG spam log.
        """
        p = int(percent)
        if self._last_battery == p:
            return
        self._last_battery = p

        if self.mode == "debug":
            print(f"[OLED DEBUG] Battery: {p}%")


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
