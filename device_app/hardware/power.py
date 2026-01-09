# device_app/hardware/power.py
from __future__ import annotations
import threading
import time
from typing import Optional


# ==========================================================
# Dummy fallback (LUÔN CHẠY ĐƯỢC)
# ==========================================================
class DummyPowerManager:
    def __init__(self):
        print("[POWER] DummyPowerManager active")

    def get_percent(self) -> Optional[int]:
        return None

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self):
        print("[POWER] Shutdown requested (dummy ignored)")


# ==========================================================
# Real PowerManager (ADS1015 – KHÔNG BLOCK)
# ==========================================================
class PowerManager:
    def __init__(self, config: dict):
        self._ok = False
        self._last_percent: Optional[int] = None

        # divider
        self.r1 = float(config.get("R1", 33000))
        self.r2 = float(config.get("R2", 100000))

        self.min_v = float(config.get("MIN_V", 3.2))
        self.max_v = float(config.get("MAX_V", 4.2))

        self._chan = None

        # ---- init ADS trong thread riêng ----
        def _init_ads():
            try:
                import board
                import busio
                from adafruit_ads1x15.ads1015 import ADS1015
                from adafruit_ads1x15.analog_in import AnalogIn

                address = int(str(config.get("I2C_ADDRESS", "0x48")), 16)

                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS1015(i2c, address=address)
                self._chan = AnalogIn(ads, 0)  # A0

                self._ok = True
                print("[POWER] ADS1015 initialized")

            except Exception as e:
                print("[POWER] Init failed:", e)

        t = threading.Thread(target=_init_ads, daemon=True)
        t.start()
        t.join(timeout=1.5)

        if not self._ok:
            raise RuntimeError("ADS1015 not available")

    # --------------------------------------------------
    def _read_vbat(self) -> float:
        if not self._chan:
            raise RuntimeError("ADC not ready")

        v_adc = self._chan.voltage
        return v_adc * (self.r1 + self.r2) / self.r2

    # --------------------------------------------------
    def get_percent(self) -> Optional[int]:
        try:
            vbat = self._read_vbat()
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception:
            return self._last_percent

    # --------------------------------------------------
    def is_low(self) -> bool:
        try:
            return self._read_vbat() < 3.3
        except Exception:
            return False

    # --------------------------------------------------
def should_shutdown(self) -> bool:
        try:
            return self._read_vbat() < 3.1
        except Exception:
            return False

    # --------------------------------------------------
    def shutdown(self):
        print("[POWER] Shutdown requested")
        import os
        os.system("sudo shutdown now")


# ==========================================================
# FACTORY (KHÔNG BAO GIỜ LÀM TREO HỆ THỐNG)
# ==========================================================
def create_power_manager(cfg: dict):
    power_cfg = cfg.get("POWER", cfg)

    try:
        return PowerManager(power_cfg)
    except Exception as e:
        print("[POWER] Fallback to DummyPowerManager:", e)
        return DummyPowerManager()