# device_app/hardware/audio.py

from abc import ABC, abstractmethod
from pathlib import Path
import time

# Thử import sounddevice + soundfile cho bản debug trên PC
try:
    import sounddevice as sd
    import soundfile as sf
except Exception:
    sd = None
    sf = None


class BaseAudio(ABC):
    @abstractmethod
    def record_once(self, mode: str) -> Path:
        """
        Ghi một đoạn audio, trả về đường dẫn file WAV.
        """
        raise NotImplementedError

    @abstractmethod
    def play(self, wav_path: str | Path) -> None:
        """Phát file WAV."""
        raise NotImplementedError


# ---------------------- DEBUG on PC ---------------------- #

class DebugAudio(BaseAudio):
    """
    Dùng trên PC:
    - Nếu có sounddevice + soundfile: ghi âm thật từ mic và phát lại.
    - Nếu không có: chỉ giả lập, in log.
    """

    def __init__(self, config):
        self.config = config
        audio_cfg = config.get("AUDIO_DEBUG", {})
        self.sample_rate = int(audio_cfg.get("SAMPLE_RATE", 16000))
        self.duration = float(audio_cfg.get("DURATION_SEC", 5))
        out_dir = audio_cfg.get("OUTPUT_DIR", "artifacts/debug_audio")
        self.output_dir = Path(out_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if sd is None or sf is None:
            print("[AUDIO DEBUG] sounddevice/soundfile not available -> using dummy mode.")
        else:
            print("[AUDIO DEBUG] Using sounddevice to record & play audio.")

    def record_once(self, mode: str) -> Path:
        """
        Ghi âm một đoạn từ mic (nếu có sounddevice),
        hoặc giả lập nếu không có.
        """
        ts = int(time.time())
        out_path = self.output_dir / f"input_{mode.replace('→', '_')}_{ts}.wav"

        if sd is None or sf is None:
            input("[AUDIO DEBUG] (DUMMY) Nhấn Enter để GIẢ LẬP: đã ghi xong 1 đoạn audio...")
            return out_path  # file không tồn tại, nhưng STT stub không cần file thật

        print(f"[AUDIO DEBUG] Recording {self.duration} s at {self.sample_rate} Hz...")
        frames = int(self.sample_rate * self.duration)
        audio = sd.rec(frames, samplerate=self.sample_rate, channels=1, dtype="float32")
        sd.wait()
        sf.write(out_path, audio, self.sample_rate)
        print(f"[AUDIO DEBUG] Saved WAV to {out_path}")
        return out_path

    def play(self, wav_path: str | Path) -> None:
        wav_path = Path(wav_path)
        if sd is None or sf is None:
            print(f"[AUDIO DEBUG] (DUMMY) Giả lập phát file: {wav_path}")
            return

        if not wav_path.exists():
            print(f"[AUDIO DEBUG] File không tồn tại: {wav_path}")
            return

        print(f"[AUDIO DEBUG] Playing {wav_path} ...")
        data, sr = sf.read(wav_path, dtype="float32")
        sd.play(data, sr)
        sd.wait()
        print("[AUDIO DEBUG] Done playing.")


# ---------------------- Pi (sau này) ---------------------- #

class PiAudio(BaseAudio):
    """
    Sau này dùng trên Raspberry Pi + ES8388:
    - record_once: dùng arecord/ALSA
    - play: dùng aplay/ALSA
    Hiện tại để TODO, chỉ in log.
    """

    def __init__(self, config):
        self.config = config
        print("[PI AUDIO] Stub backend, chưa implement arecord/aplay.")

    def record_once(self, mode: str) -> Path:
        print("[PI AUDIO] record_once() STUB – cần implement khi lên Pi.")
        # TODO: dùng subprocess.run(['arecord', ...]) để ghi âm
        return Path("pi_dummy_input.wav")

    def play(self, wav_path: str | Path) -> None:
        print(f"[PI AUDIO] play({wav_path}) STUB – cần implement khi lên Pi.")
        # TODO: subprocess.run(['aplay', ...])


def create_audio(config) -> BaseAudio:
    mode = config.get("AUDIO_MODE", "debug")
    if mode == "pi":
        return PiAudio(config)
    return DebugAudio(config)
