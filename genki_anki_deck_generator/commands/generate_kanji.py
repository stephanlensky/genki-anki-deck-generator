import argparse
import json
import os
import sys
import textwrap
from pathlib import Path

from anthropic import Anthropic, beta_tool

from genki_anki_deck_generator.template import Card, load_templates, save_template

DEFAULT_BATCH_SIZE = 20


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--template", type=str, help="Path to a specific template to process")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of cards to process in a batch",
    )
    parser.description = "Generate Kanji using AI for cards which only have Hiragana readings."


def run(args: argparse.Namespace) -> None:
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
    )

    templates_by_deck = load_templates()
    if args.template:
        templates = [
            t
            for templates in templates_by_deck.values()
            for t in templates
            if t.path.absolute() == Path(args.template).absolute()
        ]
        if not templates:
            print(f"Template {args.template} not found.")
            sys.exit(1)
    else:
        templates = [t for templates in templates_by_deck.values() for t in templates]

    for template in templates:
        cards_with_missing_kanji: list[Card] = []
        for card in template.iter_cards():
            if card.kanji is None:
                cards_with_missing_kanji.append(card)

        print(f"Found {len(cards_with_missing_kanji)} cards with missing kanji.")
        for i in range(0, len(cards_with_missing_kanji), args.batch_size):
            batch = cards_with_missing_kanji[i : i + args.batch_size]
            print(f"Detecting kanji... ({i}/{len(cards_with_missing_kanji)} completed)")
            _process_batch(client, batch)

            # save after each batch to save progress in case of interruption
            save_template(template)


def _process_batch(client: Anthropic, batch: list[Card]) -> None:
    system_prompt = textwrap.dedent("""
    You are a Japanese language assistant. Your task is to help annotate hiragana-only vocabulary
    cards with the equivalent kanji where applicable. You will be provided the hiragana reading for
    each word as well as its English meaning.

    When annotating words, you will add a new 'kanji' field to each card which contains the original
    reading, but with any kana replaced by the appropriate kanji characters if they exist. If no
    kanji exists for the word, you will omit the'kanji' field and leave the card as-is.

    Examples:
    1. Provided card - Hiragana: ねこ, English: cat
       Annotated card - Hiragana: ねこ, English: cat, Kanji: 猫
    2. Provided card - Hiragana: ありがとう, English: thank you
       Annotated card - Hiragana: ありがとう, English: thank you
    3. Provided card - Hiragana: たべる, English: to eat
       Annotated card - Hiragana: たべる, English: to eat, Kanji: 食べる
    """).strip()
    user_message = textwrap.dedent(f"""
    Annotate the following vocabulary cards with kanji where applicable.
    {json.dumps([c.to_dict() for c in batch])}
    """).strip()
    runner = client.beta.messages.tool_runner(
        model="claude-haiku-4-5",
        max_tokens=10_000,
        tools=[_final_answer],
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": user_message,
            }
        ],
    )

    global _final_answer_result
    _final_answer_result = None
    message_counter = 0
    for message in runner:
        print(f"[claude] {message}")
        if (message_counter) > 5:
            print(
                "Error: Too many messages received from Claude without final answer, something went wrong?."
            )
            break
        message_counter += 1

    if _final_answer_result is None:
        print("Error: No final answer received from Claude.")
        sys.exit(1)

    if len(_final_answer_result) != len(batch):
        print(
            f"Error: Mismatched number of cards in final answer. Expected {len(batch)}, "
            f"got {len(_final_answer_result)}."
        )
        sys.exit(1)

    for card, updated_card_data in zip(batch, _final_answer_result):
        if (
            "kanji" in updated_card_data
            # ensure that there is at least one kanji character in the provided kanji field
            # the model isn't supposed to add the field if the word contains only kana, but
            # sometimes it does anyway
            and any(
                "\u4e00" <= ch <= "\u9fff" or "\u3400" <= ch <= "\u4dbf"
                for ch in updated_card_data["kanji"]
            )
        ):
            card.kanji = updated_card_data["kanji"]
            print(
                f"Updated card: Hiragana: {card.japanese}, English: {card.english}, "
                f"Kanji: {card.kanji}"
            )
        else:
            print(f"No kanji found for card: Hiragana: {card.japanese}, English: {card.english}")


_final_answer_result: list[dict[str, str]] | None = None


@beta_tool(name="final_answer")
def _final_answer(processed_cards: list[dict]) -> str:
    """
    Return a list of processed cards with kanji readings filled in.

    Args:
        processed_cards (list[dict]): A list of dictionaries containing card information with added
        kanji readings. Cards should be in exactly the same format and order as originally provided,
        with the addition of the 'kanji' field containing the kanji representation if applicable.
    """
    global _final_answer_result
    _final_answer_result = processed_cards
    return "Final answer received."
