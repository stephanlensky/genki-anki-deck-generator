import argparse

from genki_anki_deck_generator.config import get_config
from genki_anki_deck_generator.utils.google_drive import google_drive_download
from genki_anki_deck_generator.utils.kanji_meanings import download_kanji_data


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = "Download audio files, fonts, and Kanji data for the Genki Anki decks."


def run(args: argparse.Namespace) -> None:
    print("Downloading audio files, fonts, and Kanji data...")
    config = get_config()
    audio_dir = config.download_dir / "audio"
    fonts_dir = config.download_dir / "fonts"

    for deck in config.decks:
        deck_dir = audio_dir / deck
        if not deck_dir.exists():
            google_drive_download(
                file_id=config.sources.audio[deck], destination=deck_dir, unzip=True
            )
        else:
            print(f"Skipping download of {config.decks[deck]} audio, already exists at {deck_dir}")

    if not fonts_dir.exists():
        google_drive_download(
            file_id=config.sources.fonts, destination=fonts_dir / "_NotoSansCJKjp-Regular.woff2"
        )
    else:
        print(f"Skipping download of fonts, already exists at {fonts_dir}")

    download_kanji_data(overwrite=False)
