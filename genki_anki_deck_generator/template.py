from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Generator

from yaml import safe_dump, safe_load

from genki_anki_deck_generator.config import get_config, get_deck_config
from genki_anki_deck_generator.utils.kanji_meanings import get_kanji_meanings


class VerbType(StrEnum):
    ICHIDAN = "ichidan"
    GODAN = "godan"
    IRREGULAR = "irregular"


@dataclass(kw_only=True)
class Card:
    template: Template
    japanese: str
    japanese_note: str | None = None
    english: str
    kanji: str | None = None
    kanji_readings: list[tuple[str, str]] | None = None
    verb_type: VerbType | None = None
    sound_file: str | None = None
    parent: CardCollection | None = None

    def __post_init__(self) -> None:
        self._kanji_meanings: dict[str, list[str] | None] | None = None

    @property
    def tags(self) -> list[str]:
        parent = self.parent
        tags: list[str] = []
        while parent:
            tags[:0] = parent.tags
            parent = parent.parent
        return tags

    @property
    def kanji_meanings(self) -> dict[str, list[str] | None] | None:
        """Get the meanings of the kanji in this card."""
        if not self.kanji:
            return None
        if self._kanji_meanings is not None:
            return self._kanji_meanings

        kanjis = [k for k in self.kanji if k != "."]
        self._kanji_meanings = {k: get_kanji_meanings(k) for k in kanjis}
        return self._kanji_meanings

    def __str__(self) -> str:
        return f"Card(japanese={self.japanese}, english={self.english}, kanji={self.kanji}, sound_file={self.sound_file}, tags={self.tags})"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "japanese": self.japanese,
        }
        if self.japanese_note:
            d["japanese_note"] = self.japanese_note
        d["english"] = self.english
        if self.kanji:
            d["kanji"] = self.kanji
        if self.kanji_readings:
            d["kanji_readings"] = [{k: r} for k, r in self.kanji_readings]
        if self.verb_type:
            d["verb_type"] = self.verb_type.value
        if self.sound_file:
            d["sound_file"] = str(PurePosixPath(self.sound_file))
        return d


@dataclass(kw_only=True)
class CardCollection:
    tags: list[str] = field(default_factory=list)
    vocabulary: list[Card | CardCollection] = field(default_factory=list)
    parent: CardCollection | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tags": self.tags,
            "vocabulary": [card.to_dict() for card in self.vocabulary],
        }

    def remove_card(self, card: Card) -> None:
        """Remove a card from the collection."""
        if not self._remove_card(card):
            raise ValueError(f"Card {card.japanese} not found in collection")

    def _remove_card(self, card: Card) -> bool:
        """Recursively remove a card from the collection."""
        for i in range(len(self.vocabulary) - 1, -1, -1):
            item = self.vocabulary[i]
            if item == card:
                del self.vocabulary[i]
                return True
            elif isinstance(item, CardCollection):
                if item._remove_card(card):
                    if not item.vocabulary:
                        self.vocabulary.remove(item)
                    return True
        return False


@dataclass(kw_only=True)
class Template:
    path: Path
    cards: CardCollection

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "cards": self.cards.to_dict(),
        }

    def iter_cards(self) -> Generator[Card, None, None]:
        yield from self._iter_cards(self.cards)

    def _iter_cards(self, cards: Card | CardCollection) -> Generator[Card, None, None]:
        if isinstance(cards, CardCollection):
            for card in cards.vocabulary:
                yield from self._iter_cards(card)
        else:
            yield cards

    def remove_card(self, card: Card) -> None:
        """Remove a card from the template."""
        self.cards.remove_card(card)


def load_templates() -> dict[str, list[Template]]:
    config = get_config()
    templates: dict[str, list[Template]] = {}
    for deck in config.decks:
        templates[deck] = []
        deck_config = get_deck_config(deck)
        for template_path in deck_config.templates:
            template_content = template_path.read_text(encoding="utf-8")
            template_yaml = safe_load(template_content)
            template = Template(path=template_path, cards=CardCollection())
            cards = _load_cards(template, template_yaml)
            assert isinstance(cards, CardCollection), "Template must contain a CardCollection"
            template.cards = cards
            templates[deck].append(template)

    for deck_templates in templates.values():
        deck_templates.sort(key=lambda x: x.path)

    return templates


def _load_cards(template: Template, template_yaml: dict[str, Any]) -> CardCollection | Card:
    if "vocabulary" in template_yaml:
        collection = CardCollection(
            tags=template_yaml.get("tags", []),
            vocabulary=[_load_cards(template, card) for card in template_yaml["vocabulary"]],
        )
        for card in collection.vocabulary:
            card.parent = collection
        return collection
    if "japanese" in template_yaml:
        return Card(
            template=template,
            japanese=template_yaml["japanese"],
            japanese_note=template_yaml.get("japanese_note"),
            english=template_yaml["english"],
            kanji=template_yaml.get("kanji"),
            kanji_readings=[
                (k, r)
                for reading in template_yaml.get("kanji_readings", {})
                for k, r in reading.items()
            ]
            if template_yaml.get("kanji_readings")
            else None,
            verb_type=VerbType(template_yaml["verb_type"])
            if "verb_type" in template_yaml
            else None,
            sound_file=template_yaml.get("sound_file"),
        )

    raise ValueError("Invalid template structure")


def save_template(template: Template) -> None:
    with template.path.open("w", encoding="utf-8") as f:
        content = template.cards.to_dict()
        f.write(safe_dump(content, allow_unicode=True, default_flow_style=False, sort_keys=False))
