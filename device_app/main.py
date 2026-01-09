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
from device_app.models.nlp.nlp_processor import NLPProcessorV2
from device_app.models.nlp.skeleton_translation import SkeletonTranslator


def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    # ========== HARDWARE ==========
    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    # ========== MODELS ==========
    # ========== MODELS ==========
    stt_vi = STTVi(config)
    stt_en = STTEn(config)

    nmt_vi_en = NMTViEn(config)
    nmt_en_vi = NMTEnVi(config)

    tts_vi = TTSVi(config)
    tts_en = TTSEn(config)

    # NLP: dùng chung 1 instance cho cả VI & EN
    nlp = NLPProcessorV2(config)

    # Skeleton
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
        nlp_vi=nlp,
        nlp_en=nlp,
        skeleton=skeleton,
    )

    pipeline.run(start_mode=Mode.VI_EN)


if __name__ == "__main__":
    main()
