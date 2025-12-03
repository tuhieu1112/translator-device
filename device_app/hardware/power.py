# device_app/hardware/power.py

from abc import ABC, abstractmethod
import os


class BasePower(ABC):
    @abstractmethod
    def get_battery_percent(self) -> int:
        """Trả về % pin (0–100). Nếu không đo được thì trả 100."""
        raise NotImplementedError

    def request_shutdown(self):
        """Gọi lệnh shutdown hệ thống."""
        print("[POWER] Shutdown requested")
        # Khi test trên Pi thật mới bật dòng dưới:
        # os.system("sudo poweroff")


class DebugPower(BasePower):
    def get_battery_percent(self) -> int:
        return 100  # bản demo luôn full pin


class PiPower(BasePower):
    def __init__(self, config):
        self.config = config
        # TODO: khởi tạo ADC / module đo pin nếu có

    def get_battery_percent(self) -> int:
        # TODO: đọc giá trị thực từ ADC, quy đổi về %
        return 75  # tạm thời


def create_power(config) -> BasePower:
    mode = config.get("POWER_MODE", "debug")
    if mode == "pi":
        return PiPower(config)
    return DebugPower()
