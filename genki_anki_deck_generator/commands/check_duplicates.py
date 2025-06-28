import argparse

from genki_anki_deck_generator.template import load_templates
from genki_anki_deck_generator.utils.duplicates import remove_duplicates


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = "Check decks for duplicate vocabulary words. Optionally, automatically remove them from the source YAML templates."
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Automatically remove duplicates",
    )


def run(args: argparse.Namespace) -> None:
    print("Checking decks for duplicate vocabulary words...")
    templates_by_deck = load_templates()
    remove_duplicates(templates_by_deck, save=args.remove, echo=True)
