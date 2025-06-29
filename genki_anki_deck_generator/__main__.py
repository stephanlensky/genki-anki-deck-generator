import argparse
from pathlib import Path

from genki_anki_deck_generator.commands import (
    check_duplicates,
    copy_audio_from_duplicates,
    download,
    generate,
    generate_kanji_readings,
    generate_missing_audio,
    match_vocab,
    process_audio,
)
from genki_anki_deck_generator.config import (
    CONFIG_PATH,
    DECKS_PATH,
    set_config_path,
    set_decks_path,
)


def main() -> None:
    commands = {
        "download": download,
        "process-audio": process_audio,
        "generate": generate,
        "match-vocab": match_vocab,
        "check-duplicates": check_duplicates,
        "copy-audio-from-duplicates": copy_audio_from_duplicates,
        "generate-missing-audio": generate_missing_audio,
        "generate-kanji-readings": generate_kanji_readings,
    }

    parser = argparse.ArgumentParser(
        description="Generate Genki Anki decks from official Genki audio files"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=f"{CONFIG_PATH}",
        help=f"Path to the configuration file (default: {CONFIG_PATH})",
    )
    parser.add_argument(
        "--decks",
        "-d",
        type=str,
        default=f"{DECKS_PATH}",
        help=f"Path to the decks directory (default: {DECKS_PATH})",
    )

    subparsers = parser.add_subparsers(dest="subcommand")
    for command_name in commands:
        command_parser = subparsers.add_parser(command_name)
        commands[command_name].add_arguments(command_parser)

    args = parser.parse_args()
    set_config_path(Path(args.config))
    set_decks_path(Path(args.decks))

    if command := commands.get(args.subcommand):
        command.run(args)
    else:
        download.run(args)
        process_audio.run(args)
        generate.run(args)


if __name__ == "__main__":
    main()
