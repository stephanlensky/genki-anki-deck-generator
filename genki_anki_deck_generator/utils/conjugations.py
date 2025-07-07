from typing import TypedDict

from japanese_verb_conjugator_v2 import VerbClass, generate_japanese_verb_by_str

from genki_anki_deck_generator.template import Card, VerbType


class ConjugationDict(TypedDict):
    plain: str
    past: str
    negative: str
    polite: str
    # TODO: Add more conjugations as needed


def get_conjugations(card: Card) -> ConjugationDict | None:
    if card.verb_type is None:
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

    return ConjugationDict(
        plain=plain,
        past=past,
        negative=negative,
        polite=polite,
    )


def _get_verb_class(card: Card) -> VerbClass:
    if card.verb_type == VerbType.ICHIDAN:
        return VerbClass.ICHIDAN
    elif card.verb_type == VerbType.GODAN:
        return VerbClass.GODAN
    elif card.verb_type == VerbType.IRREGULAR:
        return VerbClass.IRREGULAR
    else:
        raise ValueError(f"Unknown verb type: {card.verb_type}")
