from abc import ABC, abstractmethod
from pathlib import Path


class BaseAudio(ABC):
    @abstractmethod
    def record_once(self, mode: str) -> Path:
        """
        Ghi một đoạn audio, trả về đường dẫn file WAV.
        Bản debug không cần file thật, chỉ giả lập.
        """
        raise NotImplementedError

    @abstractmethod
    def play(self, wav_path: str | Path) -> None:
        """Phát file WAV (bản debug chỉ in ra màn hình)."""
        raise NotImplementedError


class DebugAudio(BaseAudio):
    """Dùng trên PC: chỉ giả lập, không thực sự ghi/phát âm thanh."""

    def __init__(self, config):
        self.config = config

    def record_once(self, mode: str) -> Path:
        input("[AUDIO DEBUG] Nhấn Enter để GIẢ LẬP: đã ghi xong 1 đoạn audio...")
        # không dùng file thật nên trả về đường dẫn “ảo”
        return Path("dummy_input.wav")

    def play(self, wav_path: str | Path) -> None:
        print(f"[AUDIO DEBUG] Giả lập phát file: {wav_path}")


class PiAudio(BaseAudio):
    """
    Sau này dùng trên Raspberry Pi + ES8388:
    - record_once: dùng arecord/ALSA
    - play: dùng aplay/ALSA
    Hiện tại để TODO.
    """

    def __init__(self, config):
        self.config = config
        # TODO: cấu hình ALSA / ES8388

    def record_once(self, mode: str) -> Path:
        # TODO: ghi âm thật trên Pi
        return Path("dummy_input_pi.wav")

    def play(self, wav_path: str | Path) -> None:
        # TODO: phát âm thanh thật trên Pi
        pass


def create_audio(config) -> BaseAudio:
    mode = config.get("AUDIO_MODE", "debug")
    if mode == "pi":
        return PiAudio(config)
    return DebugAudio(config)
