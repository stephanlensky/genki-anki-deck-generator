from typing import TypedDict

from japanese_verb_conjugator_v2 import VerbClass, generate_japanese_verb_by_str

from genki_anki_deck_generator.template import Card, VerbGroup


class ConjugationDict(TypedDict):
    polite: str
    past: str
    negative: str
    # TODO: Add more conjugations as needed


def get_conjugations(card: Card) -> ConjugationDict | None:
    if card.verb_group is None:
        return None

    verb_class = _get_verb_class(card)
    japanese = card.kanji if card.kanji else card.japanese
    try:
        plain = generate_japanese_verb_by_str(japanese, verb_class, "pla")
        polite = generate_japanese_verb_by_str(plain, verb_class, "pol")
        past = generate_japanese_verb_by_str(plain, verb_class, "pla", "past")
        negative = generate_japanese_verb_by_str(plain, verb_class, "pla", "neg")
    except Exception as e:
        print(f"Error generating conjugations for {japanese}: {e}")
        return None

    return ConjugationDict(polite=polite, past=past, negative=negative)


def _get_verb_class(card: Card) -> VerbClass:
    if card.verb_group == VerbGroup.ICHIDAN:
        return VerbClass.ICHIDAN
    elif card.verb_group == VerbGroup.GODAN:
        return VerbClass.GODAN
    elif card.verb_group == VerbGroup.IRREGULAR:
        return VerbClass.IRREGULAR
    else:
        raise ValueError(f"Unknown verb group: {card.verb_group}")


def get_conjugation_display_names() -> ConjugationDict:
    return ConjugationDict(
        polite="〜ます",
        past="Past",
        negative="Negative",
    )


def get_conjugation_links() -> ConjugationDict:
    return ConjugationDict(
        polite="https://jpdb.io/conjugation/verb/%E3%81%BE%E3%81%99",
        past="https://jpdb.io/conjugation/verb/%E3%81%9F",
        negative="https://jpdb.io/conjugation/verb/%E3%81%AA%E3%81%84",
    )
