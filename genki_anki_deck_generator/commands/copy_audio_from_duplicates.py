import argparse

from genki_anki_deck_generator.template import load_templates, save_template
from genki_anki_deck_generator.utils.duplicates import find_duplicates


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace) -> None:
    print("Checking decks for duplicates with missing audio...")
    templates_by_deck = load_templates()
    duplicates = find_duplicates(templates_by_deck, echo=True)
    for duplicate_list in duplicates:
        cards_with_sound_file = [card for card in duplicate_list if card.sound_file is not None]
        cards_without_sound_file = [card for card in duplicate_list if card.sound_file is None]
        if not cards_with_sound_file:
            print("No audio files found for duplicate cards:")
            for card in cards_without_sound_file:
                print(f" - {card.template.path}: {card.japanese} - {card.english}")
            continue

        if cards_without_sound_file:
            sound_file = cards_with_sound_file[0].sound_file
            print(f"Adding audio file {sound_file} to duplicate cards:")
            for card in cards_without_sound_file:
                card.sound_file = sound_file
                print(f" - {card.template.path}: {card.japanese} - {card.english}")
                save_template(card.template)
