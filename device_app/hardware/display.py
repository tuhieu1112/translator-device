from __future__ import annotations

from typing import Any

import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306


class Display:
    """
    OLED SSD1306 display backend (REAL DEVICE)

    Hiển thị:
    - MODE
    - STATUS
    - MESSAGE
    - BATTERY (%)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.mode = str(config.get("DISPLAY_MODE", "debug")).lower()
        self._last_battery: int | None = None

        if self.mode != "oled":
            print("[DISPLAY] Running in debug mode")
            return

        # ---- I2C + OLED INIT ----
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c, addr=0x3C)

        self.oled.fill(0)
        self.oled.show()

        self.image = Image.new("1", (128, 64))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

        print("[DISPLAY] OLED SSD1306 initialized")

    # ---------------- INTERNAL ----------------

    def _render(self, lines: list[str]) -> None:
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)

        y = 0
        for line in lines[:4]:
            self.draw.text((0, y), line, font=self.font, fill=255)
            y += 16

        self.oled.image(self.image)
        self.oled.show()

    def _map_state(self, state: str | None) -> str:
        if not state:
            return ""
        return {
            "READY": "READY",
            "RECORDING": "Listening",
            "TRANSLATING": "Translating",
            "SPEAKING": "Speaking",
        }.get(state.upper(), state)

    # ---------------- PUBLIC API ----------------

    def show_status(
        self,
        text: str = "",
        battery: int | float | None = None,
        mode: Any | None = None,
        state: str | None = None,
        **kwargs,
    ) -> None:
        if self.mode != "oled":
            print("[OLED DEBUG]", text)
            return

        lines: list[str] = []

        # Line 1: MODE + BAT
        if mode:
            m = getattr(mode, "short_label", mode.name)
            header = f"{m}"
        else:
            header = "MODE"

        if battery is not None:
            header = f"{header}  {int(battery)}%"

        lines.append(header)

        # Line 2: STATUS
        status = self._map_state(state)
        lines.append(status)

        # Line 3-4: TEXT
        if text:
            lines.extend(text[:32].split("\n")[:2])

        self._render(lines)

    def show_mode(self, mode: Any, battery: int | float | None = None) -> None:
        self.show_status(
            text="Press TALK",
            battery=battery,
            mode=mode,
            state="READY",
        )

    def show_battery(self, percent: int | float) -> None:
        p = int(percent)
        if self._last_battery == p:
            return
        self._last_battery = p

        # refresh header only
        self.show_status(battery=p)


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
