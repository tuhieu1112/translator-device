import uuid
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.signal import resample_poly


class create_audio:
    def __init__(
        self,
        hw_sr=48000,
        stt_sr=16000,
        channels=1,
        input_device=None,
        output_device=None,
    ):
        self.hw_sr = hw_sr
        self.stt_sr = stt_sr
        self.channels = channels
        self.input_device = input_device
        self.output_device = output_device

        self._frames = []
        self._stream = None

        print(
            f"[AUDIO] Init | HW_SR={hw_sr} | STT_SR={stt_sr} | CH={channels} "
            f"| IN_DEV={input_device} | OUT_DEV={output_device}"
        )

    # ===============================
    # RECORD
    # ===============================

    def start_record(self):
        self._frames = []

        def callback(indata, frames, time, status):
            if status:
                print("[AUDIO] input status:", status)
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.hw_sr,
            channels=self.channels,
            dtype="float32",
            callback=callback,
            device=self.input_device,
        )
        self._stream.start()
        print("[AUDIO] Recording started")

    def stop_record(self) -> str:
        self._stream.stop()
        self._stream.close()

        audio = np.concatenate(self._frames, axis=0).squeeze()
        print(f"[AUDIO] Frames collected: {len(audio)}")

        # ===== RAW SAVE (48k) =====
        uid = uuid.uuid4().hex[:8]
        raw_path = f"/tmp/rec_{uid}_48k.wav"
        sf.write(raw_path, audio, self.hw_sr, subtype="PCM_16")
        print(f"[AUDIO] RAW saved: {raw_path}")

        # ===== STATS (48k) =====
        self._log_stats(audio, self.hw_sr, tag="RAW-48k")

        # ===== RESAMPLE → 16k FOR STT =====
        audio_16k = resample_poly(audio, self.stt_sr, self.hw_sr)

        stt_path = f"/tmp/rec_{uid}_16k.wav"
        sf.write(stt_path, audio_16k, self.stt_sr, subtype="PCM_16")
        print(f"[AUDIO] STT WAV saved: {stt_path}")

        # ===== STATS (16k) =====
        self._log_stats(audio_16k, self.stt_sr, tag="STT-16k")

        return stt_path

    # ===============================
    # PLAY (FOR TTS)
    # ===============================

    def play(self, audio: np.ndarray, sr: int):
        print(f"[AUDIO] Play | SR={sr} | len={len(audio)}")
        self._log_stats(audio, sr, tag="TTS-OUT")

        sd.play(audio, sr, device=self.output_device)
        sd.wait()

    # ===============================
    # UTILS
    # ===============================

    @staticmethod
    def _log_stats(audio: np.ndarray, sr: int, tag="AUDIO"):
        if len(audio) == 0:
            print(f"[{tag}] EMPTY AUDIO")
            return

        rms = float(np.sqrt(np.mean(audio**2)))
        peak = float(np.max(np.abs(audio)))
        clip = float(np.mean(np.abs(audio) > 0.99))
        dc = float(np.mean(audio))

        print(
            f"[{tag}] SR={sr} | len={len(audio)} | "
            f"RMS={rms:.4f} | Peak={peak:.3f} | Clip={clip:.4f} | DC={dc:.5f}"
        )
