import argparse
from pathlib import Path, PurePosixPath

import genanki

from genki_anki_deck_generator.config import get_config
from genki_anki_deck_generator.template import Card, Template, load_templates

HTML_KANJI_KANA_QUESTION = """
{{#kanji}}
<p lang="jp">
<span class="furigana hidden">{{japanese_kana}}</span><br />
<span class="kanji">{{kanji}}</span>
</p>
{{/kanji}}
{{^kanji}}
<p lang="jp" class="kana-only">{{japanese_kana}}</p>
{{/kanji}}
"""
HTML_KANJI_KANA_ANSWER = """
{{#kanji}}
<p lang="jp">
<span class="furigana">{{japanese_kana}}</span><br />
<span class="kanji">{{kanji}}</span>
</p>
{{/kanji}}
{{^kanji}}
<p lang="jp" class="kana-only">{{japanese_kana}}</p>
{{/kanji}}
"""

HTML_SOUND = """
{{#sound}}
<div class="spacer"></div>
{{sound}}
{{/sound}}
"""
HTML_FRONT_SIDE = """
<div class="frontside">
{{FrontSide}}
</div>
<div class="spacer"></div>
"""
HTML_ENGLISH = """
<p>{{english}}</p>
"""
HTML_ENGLISH_MEANING = """
<p class="heading">Meaning:</p>
<p>{{english}}</p>
"""
HTML_JAPANESE = """
<p class="heading">Japanese:</p>
"""
HTML_KANJI_MEANING = """
{{#kanji_meaning}}
<div class="spacer"></div>
<p class="heading">Kanji meaning:</p>
<p lang="jp">
{{kanji}}<br />
{{kanji_meaning}}
</p>
{{/kanji_meaning}}
"""
CSS = """

@font-face {
  font-family: "Noto Sans Japanese";
  src: url("_NotoSansCJKjp-Regular.woff2") format("woff2");
}

.card {
  font-family: "Noto Sans Japanese";
  font-size: 30px;
  text-align: center;
}

p {
  font-size: 1em;
  margin: 0;
  padding: 0;
}

.heading {
  font-size: 0.9em;
  color: var(--fg-subtle, #BBB);
}

.spacer {
  height: 1em;
}

.kana-only {
  font-size: 1.4em;
}

.kanji {
  font-size: 2em;
}

.furigana {
  font-size: 1.2em;
}

.hidden:not(.frontside *) {
  color: var(--fg, #DDD);
  background: var(--fg, #DDD);
  border:1px solid var(--fg, #DDD);
  border-radius:10px;
}

.hidden:hover:hover:not(.frontside *) {
  background:none;
  border-color:transparent;
}
"""


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def run(args: argparse.Namespace) -> None:
    print("Generating Anki decks...")
    config = get_config()
    templates_by_deck = load_templates()

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
                    Path("sources/audio") / deck / card.sound_file if card.sound_file else None
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
        kanji_meanings = (
            [meaning[0] for meaning in card.kanji_meanings if meaning]
            if card.kanji_meanings
            else []
        )
        sort_id = f"{deck}::{template.path}::{template_card_index:03d}"
        guid = genanki.guid_for(
            "genki_anki_deck_generator", deck, str(template.path), card.japanese
        )
        super().__init__(
            model=model,
            fields=[
                card.japanese,
                card.kanji if card.kanji else "",
                card.english,
                ", ".join(kanji_meanings),
                f"[sound:{PurePosixPath(qualified_sound_file_path).name}]"
                if qualified_sound_file_path
                else "",
                sort_id,
            ],
            tags=[tag.replace(" ", "_") for tag in card.tags],
            due=card_index,
            guid=guid,
        )


def get_anki_model() -> genanki.Model:
    anki_model = genanki.Model(
        1561628563,
        "Simple Model",
        fields=[
            {"name": "japanese_kana"},
            {"name": "kanji"},
            {"name": "english"},
            {"name": "kanji_meaning"},
            {"name": "sound"},
            {"name": "sort_id"},
        ],
        templates=[
            {
                "name": "japanese -> english",
                "qfmt": HTML_KANJI_KANA_QUESTION,
                "afmt": HTML_FRONT_SIDE + HTML_ENGLISH_MEANING + HTML_KANJI_MEANING + HTML_SOUND,
            },
            {
                "name": "english -> japanese",
                "qfmt": HTML_ENGLISH,
                "afmt": HTML_FRONT_SIDE
                + HTML_JAPANESE
                + HTML_KANJI_KANA_ANSWER
                + HTML_KANJI_MEANING
                + HTML_SOUND,
            },
        ],
        css=CSS,
        sort_field_index=5,  # sort_id
    )
    return anki_model


def add_media_file(media_files: dict[str, Path], file: Path) -> None:
    if not file.exists():
        raise FileNotFoundError(f"Media file {file} does not exist.")
    if file.name in media_files:
        raise ValueError(
            f"Cannot add file {file} (file with the same name already exists at {media_files[file.name]})."
        )
    media_files[file.name] = file
