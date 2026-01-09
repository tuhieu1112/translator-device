# device_app/hardware/power.py
from __future__ import annotations

import time
import os
from typing import Any, Mapping

# ==========================================================
# DUMMY POWER (fallback – không bao giờ crash pipeline)
# ==========================================================
class DummyPowerManager:
    def __init__(self, *_):
        self._pct = 100
        print("[POWER] Using DummyPowerManager")

    def get_percent(self) -> int:
        return self._pct

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Dummy shutdown (ignored)")


# ==========================================================
# REAL POWER MANAGER (ADS1015)
# ==========================================================
class PowerManager:
    def __init__(self, cfg: Mapping[str, Any]):
        # ---------- CONFIG ----------
        self.r1 = float(cfg.get("R1", 330000))   # TOP resistor (ohm)
        self.r2 = float(cfg.get("R2", 100000))   # BOTTOM resistor (ohm)

        self.min_v = float(cfg.get("MIN_V", 3.2))
        self.max_v = float(cfg.get("MAX_V", 4.2))

        self.i2c_bus = int(cfg.get("I2C_BUS", 1))
        addr_raw = cfg.get("I2C_ADDRESS", "0x48")
        self.address = int(str(addr_raw), 16)

        self.channel = int(cfg.get("CHANNEL", 0))  # A0 default

        self._last_percent: int | None = None
        self._last_vbat: float | None = None

        # ---------- IMPORTS ----------
        import board
        import busio
        from adafruit_ads1x15.ads1015 import ADS1015
        from adafruit_ads1x15.analog_in import AnalogIn

        # ---------- INIT I2C (retry-safe) ----------
        self.i2c = busio.I2C(board.SCL, board.SDA)

        retry = 0
        while not self.i2c.try_lock():
            time.sleep(0.05)
            retry += 1
            if retry > 50:
                raise RuntimeError("I2C bus not ready")

        self.i2c.unlock()

        self.ads = ADS1015(self.i2c, address=self.address)
        self.chan = AnalogIn(self.ads, self.channel)

        print(
            f"[POWER] ADS1015 initialized "
            f"(addr=0x{self.address:02X}, A{self.channel})"
        )

    # ======================================================
    # INTERNAL
    # ======================================================
    def _read_vbat(self) -> float:
        """
        Đọc điện áp pin sau cầu chia
        """
        v_adc = float(self.chan.voltage)
        vbat = v_adc * (self.r1 + self.r2) / self.r2
        self._last_vbat = vbat
        return vbat

    # ======================================================
    # PUBLIC API (pipeline dùng)
    # ======================================================
    def get_percent(self) -> int:
        try:
            v = self._read_vbat()
            pct = int(100 * (v - self.min_v) / (self.max_v - self.min_v))
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
# FACTORY (QUAN TRỌNG – KHÔNG ĐƯỢC SAI)
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