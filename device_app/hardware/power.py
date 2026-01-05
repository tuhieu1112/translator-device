from __future__ import annotations
import os


class PowerManager:
    """
    Power manager for battery-powered device

    - Read voltage from TP4056 OUT via ADS1015
    - Convert voltage to battery percentage
    - Trigger safe shutdown when battery is low
    """

    def __init__(
        self,
        channel: int = 0,
        r1: int = 100_000,
        r2: int = 100_000,
        low_voltage: float = 3.2,
    ) -> None:
        # Import hardware libraries at runtime
        # → tránh crash khi chạy DEV / test / không có I2C
        import board
        import busio
        import adafruit_ads1x15.ads1015 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn

        self.ratio = (r1 + r2) / r2
        self.low_voltage = low_voltage

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1015(i2c)
        ads.gain = 1  # ±4.096V

        self.chan = AnalogIn(ads, getattr(ADS, f"P{channel}"))

        print("[POWER] ADS1015 initialized")

    # ================= PUBLIC API =================

    def get_voltage(self) -> float:
        """Return battery voltage after divider compensation"""
        return round(self.chan.voltage * self.ratio, 2)

    def get_percent(self) -> int:
        """Estimate battery percentage from voltage"""
        v = self.get_voltage()

        if v >= 4.2:
            return 100
        if v >= 4.0:
            return 80
        if v >= 3.8:
            return 60
        if v >= 3.7:
            return 50
        if v >= 3.6:
            return 40
        if v >= 3.5:
            return 20
        return 0

    def is_low(self) -> bool:
        """Check if battery is below safe threshold"""
        return self.get_voltage() <= self.low_voltage

    def shutdown(self) -> None:
        """Shutdown system safely"""
        print("[POWER] Shutdown system")
        os.system("sudo shutdown now")


# ================= FACTORY =================


def create_power_manager(config=None) -> PowerManager:
    """
    Factory function for PowerManager

    - Giữ interface thống nhất với main.py
    - Dễ mở rộng nếu sau này đọc config.yaml
    """
    print("[POWER] Using PowerManager (ADS1015)")
    return PowerManager()
