import argparse
import shutil
import sys

from genki_anki_deck_generator.config import get_config, get_deck_config
from genki_anki_deck_generator.utils.sound import split_audio_file


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--reprocess",
        "-r",
        action="store_true",
        help="Reprocess audio files even if the target directory already exists and is not empty.",
    )


def run(args: argparse.Namespace) -> None:
    print("Processing audio files...")
    reprocess = getattr(args, "reprocess", False)
    config = get_config()
    to_process = []
    for deck_name in config.decks:
        deck_config = get_deck_config(deck_name)
        audio_dir = config.download_dir / "audio" / deck_name
        for audio_file in deck_config.audio:
            sound_file = audio_dir / audio_file.sound_file
            if not sound_file.exists():
                print(f"Error: Audio file {sound_file} does not exist!")
                sys.exit(1)

            target_dir = sound_file.parent / sound_file.stem
            if target_dir.is_dir() and any(target_dir.iterdir()):
                if reprocess:
                    shutil.rmtree(target_dir, ignore_errors=True)
                else:
                    print(f"Skipping {sound_file}, target directory exists and is not empty.")
                    continue

            overrides = audio_file.overrides or {}
            to_process.append(
                (
                    sound_file,
                    target_dir,
                    audio_file.sound_silence_threshold,
                    overrides,
                )
            )

    for sound_file, target_dir, silence_threshold, overrides in to_process:
        print(f"Processing audio file: {sound_file} -> {target_dir}")
        try:
            split_audio_file(
                file=sound_file,
                target_dir=target_dir,
                sound_silence_threshold=silence_threshold,
                overrides=overrides,
            )
        except KeyboardInterrupt:
            print("Interrupted! Deleting partially processed directory")
            shutil.rmtree(target_dir, ignore_errors=True)
            raise
