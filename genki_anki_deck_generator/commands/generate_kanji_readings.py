import argparse
import sys

import jaconv
from fugashi import Tagger  # type: ignore

from genki_anki_deck_generator.template import Card, load_templates, save_template


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = "Generate readings for Kanji cards using a fugashi / jaconv."


def run(args: argparse.Namespace) -> None:
    templates_by_deck = load_templates()
    cards_with_missing_readings: list[Card] = []
    for templates in templates_by_deck.values():
        for template in templates:
            for card in template.iter_cards():
                if card.kanji_readings is None and card.kanji is not None:
                    cards_with_missing_readings.append(card)

    if not cards_with_missing_readings:
        print("No cards with missing readings found.")
        return
    print(f"Found {len(cards_with_missing_readings)} cards with missing readings.")

    for card in cards_with_missing_readings:
        assert card.kanji is not None, "Card must have Kanji to generate readings"
        card.kanji_readings = generate_kanji_readings(card.kanji)
        if not card.kanji_readings:
            print(f"Warning: No readings generated for {card.kanji}. Please check the Kanji.")
            continue
        print(card.kanji, card.kanji_readings)

        generated_reading = card.kanji
        for kanji, reading in card.kanji_readings:
            generated_reading = generated_reading.replace(kanji, reading, 1)
        if card.japanese != generated_reading:
            print(
                f"Warning: generated reading {generated_reading} does not match original reading: {card.kanji} ({card.japanese})",
            )
            correct_readings(card.kanji_readings)

        save_template(card.template)


def correct_readings(readings: list[tuple[str, str]]) -> None:
    for i, (kanji, reading) in enumerate(readings):
        try:
            corrected_reading = input(f"Correct reading for {kanji} ({reading}): ")
        except KeyboardInterrupt:
            print("Exiting!")
            sys.exit(1)
        if corrected_reading:
            readings[i] = (kanji, corrected_reading)


def generate_kanji_readings(kanji: str) -> list[tuple[str, str]]:
    """Generate readings for the given Kanji string."""
    tagger = Tagger()
    words = tagger(kanji)
    readings = []
    for word in words:
        if all(_is_kana(char) or _is_fullwidth(char) or ord(char) < 255 for char in word.surface):
            # Skip words that do not have kanji characters
            continue
        hira = jaconv.kata2hira(word.feature.kana)
        prefix = _common_prefix([hira, word.surface])
        suffix = _common_suffix([hira, word.surface])
        kanji = word.surface.removesuffix(suffix)
        kanji = kanji.removeprefix(prefix)
        hira = hira.removeprefix(prefix)
        hira = hira.removesuffix(suffix)
        if kanji and hira:
            readings.append((kanji, hira))

    return readings


def _common_prefix(strings: list[str]) -> str:
    """Find the longest common prefix among a list of strings."""
    if not strings:
        return ""
    prefix = strings[0]
    for string in strings[1:]:
        while not string.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


def _common_suffix(strings: list[str]) -> str:
    """Find the longest common suffix among a list of strings."""
    if not strings:
        return ""
    reversed_strings = [s[::-1] for s in strings]
    prefix = _common_prefix(reversed_strings)
    return prefix[::-1]  # Reverse back to get the suffix


def _is_kana(char: str) -> bool:
    """Check if a character is a Kana character."""
    return (
        "\u3040" <= char <= "\u309f"  # Hiragana
        or "\u30a0" <= char <= "\u30ff"  # Katakana
    )


def _is_fullwidth(char: str) -> bool:
    """Check if a character is a fullwidth character."""
    return ord(char) >= 0xFF01 and ord(char) <= 0xFF5E  # Fullwidth ASCII range
