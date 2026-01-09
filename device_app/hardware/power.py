# device_app/hardware/power.py
from __future__ import annotations
from typing import Mapping, Any
import time
import os

# =======================
# REAL POWER (ADS1015)
# =======================
try:
    import board
    import busio
    from adafruit_ads1x15.ads1015 import ADS1015
    from adafruit_ads1x15.analog_in import AnalogIn
except Exception as e:
    ADS1015 = None
    print("[POWER] ADS1015 import failed:", e)


class PowerManager:
    def __init__(self, config: Mapping[str, Any]):
        # ---- Voltage divider ----
        self.r1 = float(config.get("R1", 330000))  # FIX: 330k
        self.r2 = float(config.get("R2", 100000))

        # ---- Battery range ----
        self.min_v = 3.2
        self.max_v = 4.2

        # ---- I2C ----
        address = int(str(config.get("I2C_ADDRESS", "0x48")), 16)

        if ADS1015 is None:
            raise RuntimeError("ADS1015 library not available")

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS1015(self.i2c, address=address)
        self.chan = AnalogIn(self.ads, 0)  # A0

        self._last_percent: int | None = None
        self._last_read_ts = 0.0

        print("[POWER] ADS1015 initialized")

    # ---------- Low-level ----------
    def read_vbat(self) -> float:
        v_adc = self.chan.voltage
        vbat = v_adc * (self.r1 + self.r2) / self.r2
        return vbat

    # ---------- Public API ----------
    def get_percent(self) -> int:
        # chống spam + jitter
        now = time.time()
        if now - self._last_read_ts < 1.0 and self._last_percent is not None:
            return self._last_percent

        try:
            vbat = self.read_vbat()
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))

            self._last_percent = pct
            self._last_read_ts = now
            return pct
        except Exception as e:
            print("[POWER] read error:", e)
            return self._last_percent if self._last_percent is not None else 0

    def is_low(self) -> bool:
        try:
            return self.read_vbat() < 3.3
        except Exception:
            return False

    def should_shutdown(self) -> bool:
        try:
            return self.read_vbat() < 3.1
        except Exception:
            return False

    def shutdown(self) -> None:
        print("[POWER] Shutdown requested")
        # FIX: systemd-friendly (không cần sudo TTY)
        os.system("systemctl poweroff")


# =======================
# DUMMY (fallback)
# =======================
class DummyPowerManager:
    def get_percent(self) -> int:
        return 100

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self) -> None:
        print("[POWER] Dummy shutdown ignored")


# =======================
# FACTORY (BẮT BUỘC)
# =======================
def create_power_manager(cfg: Mapping[str, Any]):
    mode = str(cfg.get("POWER_MODE", "")).lower()

    if mode in ("ads1015", "ads1115"):
        print("[POWER] Using ADS1015 backend")
        return PowerManager(cfg.get("POWER", cfg))

    print("[POWER] Using DummyPowerManager")
    return DummyPowerManager()
