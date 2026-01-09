# tts_en.py
from device_app.models.piper_tts import PiperTTS


def create_tts_en(config: dict):
    """
    Example factory. config can come from your global config.
    Expected keys (optional): MODEL, VOICE, PIPER_EXE, HW_SR, OUT_DEV
    """
    model = config.get("VOICE_FILE") or config.get("MODEL")
    voice = config.get("SPEAKER") or config.get("VOICE")
    return PiperTTS(
        model=model,
        voice=voice,
        piper_exe=config.get("PIPER_EXE", "piper"),
        hw_sr=config.get("HW_SR", 48000),
        out_device=config.get("OUT_DEV"),
    )


# tts_vi.py
from piper_tts import PiperTTS


def create_tts_vi(config: dict):
    model = config.get("VOICE_FILE") or config.get("MODEL")
    voice = config.get("SPEAKER") or config.get("VOICE")
    return PiperTTS(
        model=model,
        voice=voice,
        piper_exe=config.get("PIPER_EXE", "piper"),
        hw_sr=config.get("HW_SR", 48000),
        out_device=config.get("OUT_DEV"),
    )
