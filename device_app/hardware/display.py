# device_app/hardware/display.py
from __future__ import annotations
from typing import Any, Optional

# OLED backend for SSD1306 (I2C) using adafruit_ssd1306 + PIL
# Shows: MODE (short label), STATUS (READY / Listening / Translating / Speaking), BATTERY %
# Designed to be robust: safe init, clear+redraw on every show_status, limited flicker.


class Display:
    def __init__(self, config: dict[str, Any]) -> None:
        # read display config with defaults
        disp_cfg = config.get("DISPLAY", {}) if config else {}
        self.width = int(disp_cfg.get("WIDTH", 128))
        self.height = int(disp_cfg.get("HEIGHT", 64))
        self.i2c_addr = int(disp_cfg.get("I2C_ADDRESS", 0x3C))
        self.i2c_bus = int(
            disp_cfg.get("I2C_BUS", 1)
        )  # kept for record; board library uses default pins

        self._last_battery: Optional[int] = None
        self._ok = False

        try:
            import board
            import busio
            from PIL import Image, ImageDraw, ImageFont
            import adafruit_ssd1306

            # init i2c (board pins)
            i2c = busio.I2C(board.SCL, board.SDA)

            # create display instance
            self._disp = adafruit_ssd1306.SSD1306_I2C(
                self.width, self.height, i2c, addr=self.i2c_addr
            )
            self._disp.fill(0)
            self._disp.show()

            # framebuffer
            self._Image = Image
            self._ImageDraw = ImageDraw
            # load default font (fast, guaranteed)
            try:
                self._font = ImageFont.load_default()
            except Exception:
                self._font = None

            # prepare an image buffer
            self._image = self._Image.new("1", (self.width, self.height))
            self._draw = self._ImageDraw.Draw(self._image)

            self._ok = True
            print(
                "[DISPLAY] OLED SSD1306 initialized ({:d}x{:d}) @0x{:02X}".format(
                    self.width, self.height, self.i2c_addr
                )
            )

        except Exception as e:
            # if anything fails, we still want pipeline to run
            self._ok = False
            self._disp = None
            self._image = None
            self._draw = None
            self._font = None
            print(f"[DISPLAY] OLED init failed: {e} — falling back to prints")

    # map pipeline state -> user friendly
    def _map_state(self, state: Optional[str]) -> str:
        if not state:
            return ""
        s = state.upper()
        return {
            "READY": "READY",
            "RECORDING": "Listening...",
            "TRANSLATING": "Translating...",
            "SPEAKING": "Speaking...",
            "IDLE": "READY",
        }.get(s, s)

    # internal: draw and show
    def _render(self, lines: list[str]) -> None:
        if not self._ok:
            # fallback: print to console (shouldn't be used in production but safe)
            print("[OLED DEBUG]")
            for ln in lines:
                print(ln)
            return

        # clear buffer
        self._draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        # choose vertical offsets according to height and font size
        # default font approximate height ~8, but compute if available
        try:
            if self._font:
                _, fh = self._font.getsize("A")
            else:
                fh = 8
        except Exception:
            fh = 8

        # line positions (we put three lines: header, status, hint)
        y = 0
        pad = 0
        # header (mode + battery) - slightly bigger spacing
        if lines:
            header = lines[0]
            # draw header
            if self._font:
                self._draw.text((0, y), header, font=self._font, fill=255)
            else:
                self._draw.text((0, y), header, fill=255)
            y += fh + 6

        # status
        if len(lines) > 1:
            status = lines[1]
            if self._font:
                self._draw.text((0, y), status, font=self._font, fill=255)
            else:
                self._draw.text((0, y), status, fill=255)
            y += fh + 4

        # text/hint (one line)
        if len(lines) > 2 and lines[2]:
            hint = lines[2]
            # ensure hint fits horizontally: truncate if necessary
            # approx char width = 6 px for default font -> compute max chars
            try:
                max_chars = int(self.width / 6)
            except Exception:
                max_chars = 20
            hint = hint[:max_chars]
            if self._font:
                self._draw.text((0, y), hint, font=self._font, fill=255)
            else:
                self._draw.text((0, y), hint, fill=255)

        # push framebuffer
        try:
            self._disp.image(self._image)
            self._disp.show()
        except Exception as e:
            # if writing fails, mark not ok and fallback to prints next time
            self._ok = False
            print(f"[DISPLAY] OLED write failed: {e}")

    # public API
    def show_status(
        self,
        text: str = "",
        battery: Optional[float] = None,
        mode: Any | None = None,
        state: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Show 3-line status:
           LINE1: MODE_LABEL    [BAT%]
           LINE2: STATUS (mapped)
           LINE3: text/hint
        """
        # build header
        if mode is not None:
            # mode may be Enum with short_label property
            mode_label = getattr(mode, "short_label", None) or getattr(
                mode, "name", str(mode)
            )
        else:
            mode_label = "?"

        header = f"{mode_label}"
        if battery is not None:
            try:
                header = f"{header}  {int(battery)}%"
            except Exception:
                header = f"{header}  ?%"

        status = self._map_state(state)
        hint = text or ""

        lines = [header, f"STATUS: {status}" if status else "STATUS:", hint]

        self._render(lines)

    def show_mode(self, mode: Any, battery: Optional[float] = None) -> None:
        self.show_status(text="Press TALK", battery=battery, mode=mode, state="READY")

    def show_battery(self, percent: float) -> None:
        try:
            p = int(percent)
        except Exception:
            return
        if self._last_battery == p:
            return
        self._last_battery = p
        # redraw header only via show_status retaining no extra text
        # we don't have mode/state args here; caller usually calls show_mode too
        # To be safe, just draw a minimal header with BAT only
        header = f"{p}%"
        self._render([f"BAT: {p}%", ""])


def create_display(config: dict[str, Any]) -> Display:
    return Display(config)
