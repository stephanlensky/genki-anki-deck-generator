import argparse

from genki_anki_deck_generator.template import Card, Template, load_templates, save_template


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Automatically remove duplicates",
    )


def run(args: argparse.Namespace) -> None:
    print("Checking decks for duplicate vocabulary words...")
    templates_by_deck = load_templates()
    remove_duplicates(templates_by_deck, save=args.remove)


def remove_duplicates(
    templates_by_deck: dict[str, list[Template]],
    allow_different_meanings: bool = True,
    save: bool = False,
) -> None:
    """
    Check for duplicate vocabulary words in the decks.
    If `remove` is True, automatically remove duplicates.
    """
    cards_by_word: dict[tuple[str, str | None], list[tuple[Template, Card]]] = {}
    for templates in templates_by_deck.values():
        for template in templates:
            for card in template.iter_cards():
                cards_by_word.setdefault((card.japanese, card.kanji), []).append((template, card))

    duplicate_count = 0
    for card_list in cards_by_word.values():
        if len(card_list) == 1:
            continue

        if allow_different_meanings:
            english = set(card.english for _, card in card_list)
            if len(english) > 1:
                print(
                    "Duplicate cards found with different English translations, skipping removal."
                )
                for template, card in card_list:
                    japanese = f"{card.japanese} / {card.kanji}" if card.kanji else card.japanese
                    print(f"  {template.path}: {japanese} - {card.english}")
                continue

        preferred_card = next((item for item in card_list if item[1].sound_file), card_list[0])

        card_list.remove(preferred_card)
        for template, card in card_list:
            print(f"Duplicate card found in {template.path}: {card.japanese} - {card.english}")
            duplicate_count += 1
            template.remove_card(card)
            if save:
                save_template(template)
                print(f"Removed duplicate card: {card.japanese} from {template.path}")

    if duplicate_count > 0:
        print(f"Total duplicate cards found: {duplicate_count}")
    else:
        print("No duplicate cards found.")
