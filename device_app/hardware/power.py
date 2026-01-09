from __future__ import annotations

import time
import os
from typing import Mapping, Any


# ==========================================================
# FALLBACK (KHÔNG BAO GIỜ CRASH)
# ==========================================================
class DummyPowerManager:
    def __init__(self, *_):
        self._pct = 100
        print("[POWER] DummyPowerManager active")

    def get_percent(self) -> int:
        return self._pct

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Dummy shutdown ignored")


# ==========================================================
# REAL POWER (ADS1015)
# ==========================================================
class PowerManager:
    def __init__(self, cfg: Mapping[str, Any]):
        self.r1 = float(cfg.get("R1", 330000))
        self.r2 = float(cfg.get("R2", 100000))
        self.min_v = float(cfg.get("MIN_V", 3.2))
        self.max_v = float(cfg.get("MAX_V", 4.2))

        addr_raw = cfg.get("I2C_ADDRESS", "0x48")
        self.address = int(str(addr_raw), 16)
        self.channel = int(cfg.get("CHANNEL", 0))

        self._last_percent: int | None = None

        import board
        import busio
        from adafruit_ads1x15.ads1015 import ADS1015
        from adafruit_ads1x15.analog_in import AnalogIn

        self.i2c = busio.I2C(board.SCL, board.SDA)

        for _ in range(50):
            if self.i2c.try_lock():
                self.i2c.unlock()
                break
            time.sleep(0.05)
        else:
            raise RuntimeError("I2C bus not ready")

        self.ads = ADS1015(self.i2c, address=self.address)
        self.chan = AnalogIn(self.ads, self.channel)

        print(f"[POWER] ADS1015 ready @0x{self.address:02X} A{self.channel}")

    # ---------------- INTERNAL ----------------
    def _read_vbat(self) -> float:
        v_adc = float(self.chan.voltage)
        return v_adc * (self.r1 + self.r2) / self.r2

    # ---------------- PUBLIC API ----------------
    def get_percent(self) -> int:
        try:
            vbat = self._read_vbat()
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception as e:
            print("[POWER] Read error:", e)
            return self._last_percent if self._last_percent is not None else 0

    def is_low(self) -> bool:
        try:
            return self._read_vbat() < 3.3
        except Exception:
            return False

    def should_shutdown(self) -> bool:
        try:
            return self._read_vbat() < 3.1
        except Exception:
            return False

    def shutdown(self):
        print("[POWER] Shutdown requested")
        os.system("sudo shutdown now")


# ==========================================================
# FACTORY
# ==========================================================
def create_power_manager(cfg: Mapping[str, Any]):
    power_cfg = cfg.get("POWER")

    if not power_cfg:
        print("[POWER] No POWER config → Dummy")
        return DummyPowerManager()

    try:
        return PowerManager(power_cfg)
    except Exception as e:
        print("[POWER] Init failed → Dummy fallback:", e)
        return DummyPowerManager()
