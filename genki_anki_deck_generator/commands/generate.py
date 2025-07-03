import argparse
from pathlib import Path, PurePosixPath

import genanki
import minify_html

from genki_anki_deck_generator.config import get_config
from genki_anki_deck_generator.template import Card, Template, load_templates
from genki_anki_deck_generator.utils.duplicates import remove_duplicates
from genki_anki_deck_generator.utils.jinja import render_template

HTML_SOUND = """
{{#sound}}
<div class="spacer"></div>
{{sound}}
{{/sound}}
"""


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = "Generate Anki decks from templates."


def run(args: argparse.Namespace) -> None:
    print("Generating Anki decks...")
    config = get_config()
    templates_by_deck = load_templates()

    if config.dedupe:
        remove_duplicates(templates_by_deck, echo=True)

    model = get_anki_model()
    anki_decks = []
    media_files: dict[str, Path] = {}
    for deck, templates in templates_by_deck.items():
        anki_deck = genanki.Deck(
            config.deck_ids[deck],
            config.decks[deck],
        )
        anki_decks.append(anki_deck)

        card_index = 0
        for template in templates:
            for template_card_index, card in enumerate(template.iter_cards()):
                qualified_sound_file_path: Path | None = (
                    Path("sources/audio") / card.sound_file if card.sound_file else None
                )
                note = GenkiNote(
                    model=model,
                    deck=deck,
                    template=template,
                    card=card,
                    card_index=card_index,
                    template_card_index=template_card_index,
                    qualified_sound_file_path=qualified_sound_file_path,
                )
                anki_deck.add_note(note)

                if qualified_sound_file_path:
                    add_media_file(media_files, qualified_sound_file_path)

                card_index += 1

    # Generate an Anki package with all book decks
    anki_package = genanki.Package(anki_decks)

    # Add font file
    add_media_file(media_files, config.download_dir / "fonts" / "_NotoSansCJKjp-Regular.woff2")

    anki_package.media_files = media_files.values()
    anki_package.write_to_file("genki.apkg")


class GenkiNote(genanki.Note):  # type: ignore
    def __init__(
        self,
        model: genanki.Model,
        deck: str,
        template: Template,
        card: Card,
        card_index: int,
        template_card_index: int,
        qualified_sound_file_path: Path | None,
    ) -> None:
        self.card = card
        simple_kanji_meanings = (
            {k: meaning[0] for k, meaning in card.kanji_meanings.items() if meaning}
            if card.kanji_meanings
            else {}
        )
        sort_id = f"{deck}::{template.path}::{template_card_index:03d}"
        guid = genanki.guid_for(
            "genki_anki_deck_generator", deck, str(template.path), card.japanese
        )

        context = card.to_dict()
        context["kanji_ruby_data"] = (
            get_kanji_ruby_data(
                card.kanji,
                card.kanji_readings if card.kanji_readings else [(card.kanji, card.japanese)],
            )
            if card.kanji
            else None
        )
        context["kanji_meanings"] = card.kanji_meanings if card.kanji_meanings else {}
        super().__init__(
            model=model,
            fields=[
                card.japanese,
                card.japanese_note if card.japanese_note else "",
                card.kanji if card.kanji else "",
                card.english,
                ", ".join(simple_kanji_meanings),
                f"[sound:{PurePosixPath(qualified_sound_file_path).name}]"
                if qualified_sound_file_path
                else "",
                minify_html.minify(
                    render_template(Path("japanese_question.html"), context),
                    keep_closing_tags=True,
                    minify_js=False,
                ),
                minify_html.minify(
                    render_template(Path("japanese_answer.html"), context),
                    keep_closing_tags=True,
                    minify_js=False,
                ),
                minify_html.minify(
                    render_template(Path("english_question.html"), context),
                    keep_closing_tags=True,
                    minify_js=False,
                ),
                minify_html.minify(
                    render_template(Path("english_answer.html"), context),
                    keep_closing_tags=True,
                    minify_js=False,
                ),
                sort_id,
            ],
            tags=[tag.replace(" ", "_") for tag in card.tags],
            due=card_index,
            guid=guid,
        )


def get_kanji_ruby_data(kanji: str, kanji_readings: list[tuple[str, str]]) -> list[tuple[str, str]]:
    i = 0
    j = 0
    kanji_ruby_data = []
    while j < len(kanji):
        if (
            i < len(kanji_readings)
            and kanji_readings[i][0] == kanji[j : j + len(kanji_readings[i][0])]
        ):
            reading = kanji_readings[i][1]
            kanji_ruby_data.append((kanji[j : j + len(kanji_readings[i][0])], reading))
            i += 1
            j += len(kanji_readings[i - 1][0])
        else:
            kanji_ruby_data.append((kanji[j], ""))
            j += 1
    return kanji_ruby_data


def get_anki_model() -> genanki.Model:
    anki_model = genanki.Model(
        1561628563,
        "Simple Model",
        fields=[
            {"name": "japanese_kana"},
            {"name": "japanese_note"},
            {"name": "kanji"},
            {"name": "english"},
            {"name": "kanji_meaning"},
            {"name": "sound"},
            {"name": "japanese_question"},
            {"name": "japanese_answer"},
            {"name": "english_question"},
            {"name": "english_answer"},
            {"name": "sort_id"},
        ],
        templates=[
            {
                "name": "japanese -> english",
                "qfmt": "{{japanese_question}}",
                "afmt": "{{japanese_answer}}" + HTML_SOUND,
            },
            {
                "name": "english -> japanese",
                "qfmt": "{{english_question}}",
                "afmt": "{{english_answer}}" + HTML_SOUND,
            },
        ],
        css=render_template(Path("style.css"), {}),
        sort_field_index=10,  # sort_id
    )
    return anki_model


def add_media_file(media_files: dict[str, Path], file: Path) -> None:
    if not file.exists():
        raise FileNotFoundError(f"Media file {file} does not exist.")
    if file.name in media_files:
        return
    media_files[file.name] = file
