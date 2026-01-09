# device_app/main.py
from pathlib import Path

from device_app.core.modes import Mode
from device_app.core.pipeline import TranslatorPipeline

from device_app.utils.config import load_config

# ===== HARDWARE =====
from device_app.hardware.display import create_display
from device_app.hardware.buttons import create_buttons
from device_app.hardware.audio import create_audio
from device_app.hardware.power import create_power_manager

# ===== MODELS =====
from device_app.models.stt_vi import STTVi
from device_app.models.stt_en import STTEn
from device_app.models.nmt_vi_en import NMTViEn
from device_app.models.nmt_en_vi import NMTEnVi
from device_app.models.tts_vi import TTSVi
from device_app.models.tts_en import TTSEn
from device_app.models.nlp.vi import NLPVi
from device_app.models.nlp.en import NLPEng
from device_app.models.skeleton_translation import SkeletonTranslator


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    # ========== HARDWARE ==========
    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    # ========== MODELS ==========
    stt_vi = STTVi(config)
    stt_en = STTEn(config)

    nmt_vi_en = NMTViEn(config)
    nmt_en_vi = NMTEnVi(config)

    tts_vi = TTSVi(config)
    tts_en = TTSEn(config)

    nlp_vi = NLPVi(config)
    nlp_en = NLPEng(config)

    skeleton = SkeletonTranslator(config)

    # ========== PIPELINE ==========
    pipeline = TranslatorPipeline(
        display=display,
        buttons=buttons,
        audio=audio,
        power=power,
        device_env=config.get("DEVICE_ENV", "PROD"),
        stt_vi=stt_vi,
        stt_en=stt_en,
        nmt_vi_en=nmt_vi_en,
        nmt_en_vi=nmt_en_vi,
        tts_vi=tts_vi,
        tts_en=tts_en,
        nlp_vi=nlp_vi,
        nlp_en=nlp_en,
        skeleton=skeleton,
    )

    pipeline.run(start_mode=Mode.VI_EN)


if __name__ == "__main__":