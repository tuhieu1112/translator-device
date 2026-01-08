from __future__ import annotations

from typing import Any
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from luma.core.render import canvas


class Display:
    """
    OLED SSD1306 (128x64)

    Hiển thị DUY NHẤT:
    - Mode
    - Status
    - Battery %
    """

    def __init__(self, config: dict[str, Any]) -> None:
        disp_cfg = config.get("DISPLAY", {})

        self.width = disp_cfg.get("WIDTH", 128)
        self.height = disp_cfg.get("HEIGHT", 64)

        serial = i2c(
            port=disp_cfg.get("I2C_BUS", 1),
            address=disp_cfg.get("I2C_ADDRESS", 0x3C),
        )
        self.device = ssd1306(serial, width=self.width, height=self.height)

        self._last = {"mode": None, "state": None, "battery": None}

        print("[DISPLAY] OLED SSD1306 initialized")

    # ================= PUBLIC API =================

    def show_mode(self, mode: Any, battery: int | None = None) -> None:
        self.show_status(
            mode=mode,
            state="READY",
            battery=battery,
        )

    def show_status(
        self,
        *,
        mode: Any | None = None,
        state: str | None = None,
        battery: int | float | None = None,
        **_,
    ) -> None:
        mode_name = getattr(mode, "short_label", str(mode)) if mode else "--"
        state_text = state or "--"
        bat_text = f"{int(battery)}%" if battery is not None else "--"

        # tránh redraw thừa
        if (
            self._last["mode"] == mode_name
            and self._last["state"] == state_text
            and self._last["battery"] == bat_text
        ):
            return

        self._last.update({"mode": mode_name, "state": state_text, "battery": bat_text})

        with canvas(self.device) as draw:
            draw.text((0, 0), f"MODE: {mode_name}", fill=255)
            draw.text((0, 18), f"STATE: {state_text}", fill=255)
            draw.text((0, 36), f"BAT: {bat_text}", fill=255)

    def show_battery(self, percent: int | float) -> None:
        # battery luôn được vẽ lại thông qua show_status
        pass


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
