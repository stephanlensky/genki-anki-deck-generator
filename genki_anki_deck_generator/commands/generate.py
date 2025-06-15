import argparse
from pathlib import Path, PurePosixPath

import genanki

from genki_anki_deck_generator.config import get_config
from genki_anki_deck_generator.template import Card, Template, load_templates

HTML_KANJI_KANA = """
<font lang="jp" size="6px" color="#C0C0C0"><span class="japanese">{{kanjis}}</span></font>
<br>
<font lang="jp" size="15px"><span class="japanese">{{japanese_kana}}</span></font>
<br>
"""
HTML_SOUND = """
{{sound}}
<br>
"""
HTML_FRONTSIDE = """
{{FrontSide}}
"""
HTML_MEANING = """
<font lang="jp" size="4px" color="#C0C0C0">Meaning: </font>
<br>
"""
HTML_ENGLISH = """
<font lang="jp" size="15px"><span class="text">{{english}}</span></font>
<br>
"""
HTML_KANJI_MEANING = """
<br>
{{#kanji_meaning}}
<font lang="jp" size="4px" color="#C0C0C0">Kanji Meaning: </font>
<br>
<font lang="jp" size="6px"><span class="japanese">{{kanjis}}</span></font>
<br>
<font lang="jp" size="6px"><span class="text">{{kanji_meaning}}</span></font>
<br>
{{/kanji_meaning}}
"""
CSS = """
.card {
  font-family: "Noto Sans Japanese";
  font-size: 20px;
  text-align: center;
}

@font-face {
  font-family: "Noto Sans Japanese";
  src: url("_NotoSansCJKjp-Regular.woff2") format("woff2");
}

.japanese {
 font-family: "Noto Sans Japanese";
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

        for template in templates:
            for i, card in enumerate(template.iter_cards()):
                qualified_sound_file_path: Path | None = (
                    Path("sources/audio") / deck / card.sound_file if card.sound_file else None
                )
                note = GenkiNote(
                    model=model,
                    deck=deck,
                    template=template,
                    card=card,
                    card_index=i,
                    qualified_sound_file_path=qualified_sound_file_path,
                )
                anki_deck.add_note(note)

                if qualified_sound_file_path:
                    add_media_file(media_files, qualified_sound_file_path)

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
        qualified_sound_file_path: Path | None,
    ) -> None:
        self.card = card
        kanji_meanings = (
            [meaning[0] for meaning in card.kanji_meanings if meaning]
            if card.kanji_meanings
            else []
        )
        sort_id = f"{deck}::{template.path}::{card_index}"
        guid = genanki.guid_for(
            "genki_anki_deck_generator", deck, str(template.path), card.japanese
        )
        super().__init__(
            model=model,
            fields=[
                card.japanese,
                card.kanji or "",
                card.english,
                ", ".join(kanji_meanings),
                f"[sound:{PurePosixPath(qualified_sound_file_path).name}]"
                if qualified_sound_file_path
                else "",
                sort_id,
            ],
            tags=[tag.replace(" ", "_") for tag in card.tags],
            guid=guid,
        )


def get_anki_model() -> genanki.Model:
    anki_model = genanki.Model(
        1561628563,
        "Simple Model",
        fields=[
            {"name": "japanese_kana"},
            {"name": "kanjis"},
            {"name": "english"},
            {"name": "kanji_meaning"},
            {"name": "sound"},
            {"name": "sort_id"},
        ],
        templates=[
            {
                "name": "japanese -> english",
                "qfmt": HTML_KANJI_KANA + HTML_SOUND,
                "afmt": HTML_FRONTSIDE + HTML_MEANING + HTML_ENGLISH + HTML_KANJI_MEANING,
            },
            {
                "name": "english -> japanese",
                "qfmt": HTML_ENGLISH,
                "afmt": HTML_FRONTSIDE
                + HTML_MEANING
                + HTML_KANJI_KANA
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
