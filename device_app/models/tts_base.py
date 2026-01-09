# tts_base.py
from __future__ import annotations
import abc
import os
import tempfile
from typing import Optional


class TTSBase(abc.ABC):
    """
    Base TTS interface used by the pipeline.
    Implementations must provide speak(text) and synthesize_to_file(path, text).
    """

    def __init__(self, *, hw_sr: int = 48000, out_device: Optional[int] = None) -> None:
        """
        :param hw_sr: hardware/ASLA output sample rate (e.g. 48000)
        :param out_device: optional sounddevice output device index
        """
        self.hw_sr = int(hw_sr)
        self.out_device = out_device

    @abc.abstractmethod
    def synthesize_to_file(self, path: str, text: str) -> None:
        """
        Synthesize `text` into `path` WAV file.
        Must create a readable WAV with a known sample rate (any).
        """
        raise NotImplementedError

    def speak(self, text: str) -> None:
        """
        Convenience: synthesize to a temp file, then play it (resample to hw_sr if needed).
        Pipeline should call this.
        """
        tf = tempfile.NamedTemporaryFile(prefix="tts_", suffix=".wav", delete=False)
        tf.close()
        wav_path = tf.name
        try:
            self.synthesize_to_file(wav_path, text)
            # playback + resample handled by helper below
            self._play_wav_resampled(wav_path)
        finally:
            try:
                os.unlink(wav_path)
            except Exception:
                pass

    def _play_wav_resampled(self, wav_path: str) -> None:
        """
        Read the wav file, resample if needed to self.hw_sr and play via sounddevice.
        """
        import soundfile as sf
        import sounddevice as sd
        from scipy.signal import resample_poly
        import numpy as np

        data, sr = sf.read(wav_path, dtype="float32")
        if data.ndim == 1:
            # make it (N,1) for sounddevice if needed (sounddevice accepts (N,) or (N,channels))
            pass

        if sr != self.hw_sr:
            # resample each channel independently
            if data.ndim == 1:
                data_rs = resample_poly(data, self.hw_sr, sr)
            else:
                # axis 0 is samples
                channels = []
                for ch in range(data.shape[1]):
                    channels.append(resample_poly(data[:, ch], self.hw_sr, sr))
                data_rs = np.stack(channels, axis=1)
            data = data_rs.astype("float32")
            sr = self.hw_sr

        # play (use out_device if provided)
        try:
            sd.play(data, sr, device=self.out_device)
            sd.wait()
        except Exception as e:
            # best-effort: print error but do not crash pipeline
            print("[TTS] playback error:", e)
