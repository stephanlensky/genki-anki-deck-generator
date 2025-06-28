import logging

from genki_anki_deck_generator.template import Card, Template, save_template

logger = logging.getLogger(__name__)


def find_duplicates(
    templates_by_deck: dict[str, list[Template]],
    allow_different_meanings: bool = True,
    echo: bool = False,
) -> list[list[Card]]:
    cards_by_word: dict[tuple[str, str | None], list[tuple[Template, Card]]] = {}
    for templates in templates_by_deck.values():
        for template in templates:
            for card in template.iter_cards():
                cards_by_word.setdefault((card.japanese, card.kanji), []).append((template, card))

    duplicates: list[list[Card]] = []
    for card_list in cards_by_word.values():
        if len(card_list) == 1:
            continue

        if allow_different_meanings:
            english = set(card.english for _, card in card_list)
            if len(english) > 1:
                logger.info("Skipping duplicate cards with different English translations:")
                if echo:
                    print("Skipping duplicate cards with different English translations:")
                for template, card in card_list:
                    japanese = f"{card.japanese} / {card.kanji}" if card.kanji else card.japanese
                    logger.info(f"{template.path}: {japanese} - {card.english}")
                    if echo:
                        print(f"  {template.path}: {japanese} - {card.english}")
                continue

        duplicates.append([card for _, card in card_list])

    return duplicates


def remove_duplicates(
    templates_by_deck: dict[str, list[Template]],
    allow_different_meanings: bool = True,
    save: bool = False,
    echo: bool = True,
) -> None:
    """
    Check for duplicate vocabulary words in the decks.
    If `remove` is True, automatically remove duplicates.
    """
    duplicates = find_duplicates(templates_by_deck, allow_different_meanings, echo=echo)
    duplicate_count = sum(len(dup) - 1 for dup in duplicates)
    if duplicate_count > 0:
        logger.info(f"Total duplicate cards found: {duplicate_count}")
        if echo:
            print(f"Total duplicate cards found: {duplicate_count}")
    else:
        logger.info("No duplicate cards found.")
        if echo:
            print("No duplicate cards found.")

    for duplicate_list in duplicates:
        preferred_card = next(
            (card for card in duplicate_list if card.sound_file), duplicate_list[0]
        )

        for card in duplicate_list:
            if card == preferred_card:
                continue

            logger.info(
                f"Duplicate card found in {card.template.path}: {card.japanese} - {card.english}"
            )
            if echo:
                print(
                    f"Duplicate card found in {card.template.path}: {card.japanese} - {card.english}"
                )
            card.template.remove_card(card)
            if save:
                save_template(card.template)
                logger.info(f"Removed duplicate card: {card.japanese} from {card.template.path}")
                if echo:
                    print(f"Removed duplicate card: {card.japanese} from {card.template.path}")
