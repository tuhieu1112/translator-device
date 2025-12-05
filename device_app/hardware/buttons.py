# device_app/hardware/buttons.py

from dataclasses import dataclass
import time

LONG_PRESS_SEC_DEFAULT = 5.0  # fallback nếu config không có


@dataclass
class ButtonEvent:
    """Kết quả đọc nút mode/power."""
    shutdown: bool = False
    toggle_mode: bool = False


class BaseButtons:
    def wait_talk_cycle(self):
        """
        Blocking đến khi người dùng 'giữ & nhả' nút TALK.
        """
        raise NotImplementedError

    def check_mode_or_shutdown(self) -> ButtonEvent:
        """
        Đọc nút MODE/POWER, phân biệt:
        - Nhấn ngắn: toggle_mode=True
        - Giữ >= LONG_PRESS_SEC: shutdown=True
        Hàm này nên được gọi thường xuyên khi thiết bị đang idle.
        """
        raise NotImplementedError


# ------------------ BẢN DEBUG (PC) ------------------ #

class DebugButtons(BaseButtons):
    """Bản debug dùng trên PC: điều khiển bằng Enter."""

    def wait_talk_cycle(self):
        input("Nhấn Enter để GIẢ LẬP: giữ & nhả nút TALK (bắt đầu thu/dịch)...")

    def check_mode_or_shutdown(self) -> ButtonEvent:
        # Bản đơn giản: không làm gì, luôn trả về không có sự kiện
        return ButtonEvent(toggle_mode=False, shutdown=False)


# ------------------ BẢN GPIO (Pi thật) ------------------ #

class GPIOButtons(BaseButtons):
    """
    Dùng trên Raspberry Pi:
    - TALK_PIN: giữ để thu âm, thả ra để bắt đầu dịch.
    - MODE_PIN:
        + nhấn ngắn -> đổi mode
        + giữ >= LONG_PRESS_SEC -> shutdown.
    """

    def __init__(self, config):
        buttons_cfg = config.get("BUTTONS", {})
        self.talk_pin = int(buttons_cfg.get("TALK_PIN", 17))
        self.mode_pin = int(buttons_cfg.get("MODE_PIN", 27))
        self.long_press_sec = float(
            buttons_cfg.get("LONG_PRESS_SEC", LONG_PRESS_SEC_DEFAULT)
        )

        # Trạng thái nội bộ để phát hiện nhấn/nhả
        self._mode_last_state = 1  # 1 = HIGH (nhả), 0 = LOW (nhấn)
        self._mode_press_start = None

        # Khởi tạo GPIO
        import RPi.GPIO as GPIO  # chỉ dùng trên Pi
        self.GPIO = GPIO
        GPIO.setmode(GPIO.BCM)

        # Nút kéo lên 3.3V, nhấn nối xuống GND => active LOW
        GPIO.setup(self.talk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.mode_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # ---- TALK BUTTON ---- #
    def wait_talk_cycle(self):
        """
        Chờ người dùng nhấn rồi nhả nút TALK.
        - Đợi từ trạng thái nhả -> nhấn -> nhả.
        """
        GPIO = self.GPIO

        # Đợi tới khi nút được nhấn (từ HIGH -> LOW)
        while GPIO.input(self.talk_pin) == GPIO.LOW:
            time.sleep(0.01)  # đang nhấn sẵn, đợi nhả ra trước

        # Bây giờ chờ nhấn:
        while GPIO.input(self.talk_pin) == GPIO.HIGH:
            time.sleep(0.01)

        # Đang được nhấn, chờ nhả ra:
        while GPIO.input(self.talk_pin) == GPIO.LOW:
            time.sleep(0.01)

        # Kết thúc 1 chu kỳ nhấn-giữ-nhả -> hàm trả về

    # ---- MODE/POWER BUTTON ---- #
    def check_mode_or_shutdown(self) -> ButtonEvent:
        """
        Gọi thường xuyên khi thiết bị idle để xem có:
        - nhấn ngắn -> đổi mode
        - nhấn dài -> shutdown
        Không blocking lâu.
        """
        GPIO = self.GPIO
        now = time.monotonic()
        state = GPIO.input(self.mode_pin)  # 1 = thả, 0 = nhấn

        event = ButtonEvent()

        # Chuyển từ thả -> nhấn
        if self._mode_last_state == 1 and state == 0:
            self._mode_press_start = now

        # Đang nhấn
        if self._mode_last_state == 0 and state == 0 and self._mode_press_start is not None:
            duration = now - self._mode_press_start
            if duration >= self.long_press_sec:
                # Giữ đủ lâu để shutdown
                event.shutdown = True
                # reset để không bắn nhiều lần
                self._mode_press_start = None

        # Chuyển từ nhấn -> thả (kết thúc nhấn ngắn)
        if self._mode_last_state == 0 and state == 1 and self._mode_press_start is not None:
            duration = now - self._mode_press_start
            if duration < self.long_press_sec:
                # Nhấn ngắn -> đổi mode
                event.toggle_mode = True
            self._mode_press_start = None

        self._mode_last_state = state
        return event


def create_buttons(config) -> BaseButtons:
    mode = config.get("BUTTON_MODE", "debug")
    if mode == "gpio":
        return GPIOButtons(config)
    return DebugButtons()
