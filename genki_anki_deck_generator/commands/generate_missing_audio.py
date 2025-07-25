import argparse
from hashlib import md5

from genki_anki_deck_generator.config import get_config
from genki_anki_deck_generator.template import Card, load_templates, save_template
from genki_anki_deck_generator.utils.voicevox import voicevox_tts


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = (
        "Generate missing audio files for vocabulary cards using VOICEVOX text-to-speech."
    )


def run(args: argparse.Namespace) -> None:
    config = get_config()
    templates_by_deck = load_templates()
    cards_with_missing_audio: list[Card] = []
    for templates in templates_by_deck.values():
        for template in templates:
            for card in template.iter_cards():
                if card.sound_file is None:
                    cards_with_missing_audio.append(card)

    if not cards_with_missing_audio:
        print("No cards with missing audio files found.")
        return
    print(f"Found {len(cards_with_missing_audio)} cards with missing audio files.")

    for card in cards_with_missing_audio:
        sanitized_japanese = (
            card.japanese.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "")
            .replace("?", "")
            .replace("*", "")
        )
        output_path = (
            config.download_dir / "tts" / f"{sanitized_japanese}_{_card_hash(card)[:5]}.wav"
        )
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
            japanese = f"{card.kanji} ({card.japanese})" if card.kanji else card.japanese
            print(f"Generating audio for card: {japanese} - {card.english}")
            voicevox_tts(
                text=card.kanji if card.kanji else card.japanese,
                speaker=2,
                output_path=output_path,
            )
            print(f"Audio saved to {output_path}")
        else:
            print(f"Skipping TTS generation, audio file already exists: {output_path}")

        card.sound_file = str(output_path.relative_to(config.download_dir).as_posix())
        save_template(card.template)


def _card_hash(card: Card) -> str:
    """Generate a unique hash for the card based on its content."""
    return md5(
        f"{card.template.path}{card.japanese}{card.english}{card.kanji}".encode()
    ).hexdigest()
