from __future__ import annotations
import time
from typing import Any, Mapping

try:
    import board
    import busio
    from adafruit_ads1x15.ads1015 import ADS1015
    from adafruit_ads1x15.analog_in import AnalogIn
except Exception:
    board = None
    busio = None
    ADS1015 = None
    AnalogIn = None


class PowerManager:
    def __init__(self, cfg: Mapping[str, Any]) -> None:
        self.r1 = float(cfg.get("R1", 33000))
        self.r2 = float(cfg.get("R2", 100000))
        self.min_v = float(cfg.get("MIN_V", 3.2))
        self.max_v = float(cfg.get("MAX_V", 4.2))
        self._last_percent: int | None = None

        if board is None or busio is None or ADS1015 is None:
            raise RuntimeError("I2C/ADS libs not available")

        i2c_bus = int(cfg.get("I2C_BUS", 1))
        address = int(str(cfg.get("I2C_ADDRESS", "0x48")), 16)

        # create i2c and ADS device
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            # small wait for bus to be ready
            timeout = time.time() + 2.0
            while not self.i2c.try_lock() and time.time() < timeout:
                time.sleep(0.01)
            # do not keep lock forever:
            if not self.i2c.try_lock():
                # we'll still try to create the ADS object (may succeed)
                pass
            # ADS1015 constructor will probe device
            self.ads = ADS1015(self.i2c, address=address)
            self.chan = AnalogIn(self.ads, 0)
            print(f"[POWER] ADS1015 initialized @0x{address:02x}")
        except Exception as e:
            # re-raise for caller to handle
            raise RuntimeError(f"ADS1015 init failed: {e}") from e
        finally:
            try:
                if hasattr(self, "i2c") and self.i2c.locked():
                    self.i2c.unlock()
            except Exception:
                pass

    def read_vbat(self) -> float:
        # measure ADC voltage on the analog channel and compute vbat via divider
        v_adc = float(self.chan.voltage)  # V at ADC input
        vbat = v_adc * (self.r1 + self.r2) / self.r2
        return vbat

    def get_percent(self) -> int:
        try:
            vbat = self.read_vbat()
            pct = int(100 * (vbat - self.min_v) / (self.max_v - self.min_v))
            pct = max(0, min(100, pct))
            self._last_percent = pct
            return pct
        except Exception as e:
            print("[POWER] read error:", e)
            return self._last_percent if self._last_percent is not None else 0

    def is_low(self) -> bool:
        try:
            return self.read_vbat() < (self.min_v + 0.1)
        except Exception:
            return False

    def should_shutdown(self) -> bool:
        try:
            return self.read_vbat() < (self.min_v - 0.1)
        except Exception:
            return False

    def shutdown(self) -> None:
        print("[POWER] Shutdown requested")
        import os

        os.system("sudo shutdown now")


# Dummy fallback when ADS not present
class DummyPowerManager:
    def __init__(self, cfg: Mapping[str, Any]) -> None:
        self._pct = 100
        print("[POWER] Init failed -> DummyPowerManager active")

    def read_vbat(self) -> float:
        return 4.2

    def get_percent(self) -> int:
        return self._pct

    def is_low(self) -> bool:
        return False

    def should_shutdown(self) -> bool:
        return False

    def shutdown(self) -> None:
        print("[POWER][DUMMY] Shutdown requested (no-op)")


def create_power_manager(cfg: Mapping[str, Any]) -> Any:
    # cfg should be the dict under "POWER" in config.yaml
    if not isinstance(cfg, Mapping):
        cfg = {}
    try:
        pm = PowerManager(cfg)
        return pm
    except Exception as e:
        print("[POWER] Init failed -> using DummyPowerManager:", e)
        return DummyPowerManager(cfg)
