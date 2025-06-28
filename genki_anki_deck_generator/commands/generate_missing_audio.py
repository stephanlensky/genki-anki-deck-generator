import argparse

from genki_anki_deck_generator.template import load_templates


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Generate missing audio files for vocabulary cards using VOICEVOX text-to-speech."
    )


def run(args: argparse.Namespace) -> None:
    templates_by_deck = load_templates()
    cards_with_missing_audio = []
    for templates in templates_by_deck.values():
        for template in templates:
            for card in template.iter_cards():
                if card.sound_file is None:
                    cards_with_missing_audio.append(card)

    if not cards_with_missing_audio:
        print("No cards with missing audio files found.")
        return
    print(f"Found {len(cards_with_missing_audio)} cards with missing audio files.")
    raise NotImplementedError("This command is not yet implemented.")
