from __future__ import annotations

from typing import Any
from PIL import Image, ImageDraw, ImageFont

import adafruit_ssd1306
import board
import busio


class Display:
    def __init__(self, config: dict[str, Any]) -> None:
        display_cfg = config.get("DISPLAY", {})

        self.width = int(display_cfg.get("WIDTH", 128))
        self.height = int(display_cfg.get("HEIGHT", 64))
        i2c_bus = int(display_cfg.get("I2C_BUS", 1))
        i2c_addr = int(display_cfg.get("I2C_ADDRESS", 0x3C))

        # I2C
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(
            self.width, self.height, i2c, addr=i2c_addr
        )

        self.oled.fill(0)
        self.oled.show()

        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

        self.last_battery: int | None = None

        print("[DISPLAY] OLED SSD1306 initialized")

    # =========================
    # INTERNAL
    # =========================
    def _clear(self) -> None:
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def _render(self) -> None:
        self.oled.image(self.image)
        self.oled.show()

    # =========================
    # PUBLIC API (USED BY PIPELINE)
    # =========================
    def show_mode(self, mode: Any, battery: int | None = None) -> None:
        self._clear()

        mode_text = getattr(mode, "short_label", str(mode))
        self.draw.text((0, 0), mode_text, font=self.font, fill=255)

        if battery is not None:
            self.draw.text((90, 0), f"{battery}%", font=self.font, fill=255)

        self.draw.text((0, 20), "READY", font=self.font, fill=255)

        self._render()

    def show_status(
        self,
        text: str = "",
        battery: int | None = None,
        mode: Any | None = None,
        state: str | None = None,
        **_,
    ) -> None:
        self._clear()

        # Line 1: MODE + BAT
        if mode is not None:
            mode_text = getattr(mode, "short_label", str(mode))
            self.draw.text((0, 0), mode_text, font=self.font, fill=255)

        if battery is not None:
            self.draw.text((90, 0), f"{battery}%", font=self.font, fill=255)

        # Line 2: STATE
        if state:
            self.draw.text((0, 20), state, font=self.font, fill=255)

        # Line 3: short hint
        if text:
            self.draw.text((0, 40), text[:16], font=self.font, fill=255)

        self._render()

    def show_battery(self, percent: int) -> None:
        # chỉ update khi battery đổi
        if self.last_battery == percent:
            return

        self.last_battery = percent
        # redraw nhẹ, không đổi state
        self._clear()
        self.draw.text((90, 0), f"{percent}%", font=self.font, fill=255)
        self._render()


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
