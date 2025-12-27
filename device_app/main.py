def main() -> None:
    here = Path(__file__).resolve().parent
    config = load_config(here / "config.yaml")

    display = create_display(config)
    buttons = create_buttons(config)
    audio = create_audio(config)
    power = create_power_manager(config)

    pipeline = TranslatorPipeline(
        config=config,
        display=display,
        buttons=None,  # pipeline KHÔNG BIẾT button
        audio=None,  # pipeline KHÔNG BIẾT audio
        power=power,
    )

    mode = Mode.VI_EN
    display.show_mode(mode)

    print("[MAIN] Device loop started")

    while True:
        buttons.wait_talk()
        audio.start_record()

        # chờ thả nút (push-to-talk)
        buttons.wait_talk_release()

        wav = audio.stop_record()
        pipeline.process_wav(wav, mode)
