import argparse
import json
import os
from functools import cache
from pathlib import Path, PurePosixPath

import pykakasi

from genki_anki_deck_generator.template import Card, load_templates, save_template

PROGRESS_FILE = Path("match_vocab_progress.json")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Helper script to match vocabulary cards with their corresponding sound files."
    )
    parser.add_argument(
        "--template",
        "-t",
        type=Path,
        help="Path to the template YAML file to process (default: all templates in config/decks)",
        default=None,
    )
    parser.add_argument(
        "--romaji",
        action=argparse.BooleanOptionalAction,
        help="Show romaji for Japanese words when processing audio files",
        default=True,
    )
    parser.add_argument(
        "--sound",
        action=argparse.BooleanOptionalAction,
        help="Enable sound playback when processing audio files",
        default=True,
    )
    parser.add_argument(
        "progress",
        action=argparse.BooleanOptionalAction,
        help=f"Disable saving/loading progress from {PROGRESS_FILE}",
        default=True,
    )


def run(args: argparse.Namespace) -> None:
    print("Running match_vocab!")
    print("This script will help you match vocabulary cards with their corresponding sound files.")
    print(
        "You can use 'j' to decrement the sound file index, 'k' to increment it, and 'y' to confirm it."
    )
    print("Press Ctrl+C to exit at any time, and your progress will be saved.")
    print(
        "Romaji and sound playback are enabled by default! Use '--no-romaji' and '--no-sound' to disable them."
    )
    print("If you want to process a specific template, use the '--template' option.")
    print(f"Progress will be automatically saved to {PROGRESS_FILE}.")
    print()

    enable_romaji = args.romaji
    enable_sound = args.sound
    enable_progress = args.progress

    templates_by_deck = load_templates()
    if args.template:
        template_path = args.template
        delete = []
        for deck, templates in templates_by_deck.items():
            templates = [t for t in templates if t.path == template_path]
            templates_by_deck[deck] = templates
            if not templates:
                delete.append(deck)

        for deck in delete:
            del templates_by_deck[deck]

        if not any(templates_by_deck.values()):
            print(f"Error: Template file {template_path} not found in any deck.")
            return

    if PROGRESS_FILE.exists():
        with PROGRESS_FILE.open("r", encoding="utf-8") as f:
            progress = json.load(f)
    else:
        progress = {"completed": []}

    for deck, templates in templates_by_deck.items():
        for template in templates:
            if enable_progress and template.path in progress["completed"]:
                print(f"Skipping {template.path}, already completed.")
                continue
            print("Processing:", template.path)
            cards = list(template.iter_cards())
            if not any(card.sound_file for card in cards):
                print(f"No sound files found in {template.path}, skipping...")
                continue

            for i, card in enumerate(cards):
                if not card.sound_file:
                    continue

                japanese = str(card.japanese)
                if enable_romaji:
                    kks_convert = get_kks().convert(japanese)
                    romaji = " ".join([item["hepburn"].strip() for item in kks_convert]).strip()
                    formatted_card = f"{japanese} - {romaji}"
                else:
                    formatted_card = japanese
                print(f"{formatted_card}")

                response = None
                try:
                    while True:
                        sound_file = card.sound_file
                        while response not in ("y", "j", "k", ""):
                            print(f"Sound file: {sound_file}, is this correct? (Y/j/k) ", end="")
                            if enable_sound:
                                play_sound(Path("sources/audio") / deck / sound_file)
                            response = input().strip().lower()
                        if response == "j":
                            increment_sound_index(cards[i:], -1)
                            if not (Path("sources/audio") / deck / card.sound_file).exists():
                                print(f"Error: can't decrement, {card.sound_file} does not exist.")
                                increment_sound_index(cards[i:], 1)
                        elif response == "k":
                            increment_sound_index(cards[i:], 1)
                            if not (Path("sources/audio") / deck / card.sound_file).exists():
                                print(f"Error: can't increment, {card.sound_file} does not exist.")
                                increment_sound_index(cards[i:], -1)
                        elif response == "y" or response == "":
                            break
                        response = None
                except KeyboardInterrupt:
                    print(f"\nExiting, saving progress on {template.path}...")
                    save_template(template)

                    return

            with open(template.path, "w", encoding="utf-8") as f:
                save_template(template)

            progress["completed"].append(str(template.path))
            if enable_progress:
                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(progress, f, ensure_ascii=False, indent=2)


@cache
def get_kks() -> pykakasi.kakasi:
    return pykakasi.kakasi()  # type: ignore


_pygame_initialized = False


def play_sound(file_path: Path) -> None:
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
    import pygame

    global _pygame_initialized
    if not _pygame_initialized:
        pygame.init()
        _pygame_initialized = True

    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()


def increment_sound_index(cards: list[Card], increment: int) -> None:
    for card in cards:
        sound_file = card.sound_file
        if sound_file is None:
            continue

        path = PurePosixPath(sound_file)
        filename_parts = path.stem.split("_")
        index = int(filename_parts[-1])
        index += increment
        new_filename = "_".join(filename_parts[:-1]) + f"_{index}"
        card.sound_file = str(path.with_name(new_filename).with_suffix(path.suffix))
