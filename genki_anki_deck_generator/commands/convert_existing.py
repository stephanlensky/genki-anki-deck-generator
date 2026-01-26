import argparse
import json
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NewType

from genki_anki_deck_generator.config import DECKS_PATH
from genki_anki_deck_generator.template import Card, CardCollection, Template, save_template

DeckId = NewType("DeckId", int)
ModelId = NewType("ModelId", int)


@dataclass
class Note:
    id: int
    model_id: ModelId
    fields: list[str]


@dataclass
class Deck:
    id: DeckId
    name: str
    notes: dict[ModelId, list[Note]]


@dataclass
class Collection:
    decks: list[Deck]


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.description = "Converts an existing Anki .apkg deck into YAML templates."
    parser.add_argument(
        "--deck-id",
        type=int,
        help="Filter notes by the specified Anki deck ID",
    )
    parser.add_argument(
        "--model-id",
        type=int,
        help="Filter notes by the specified Anki model ID",
    )
    parser.add_argument(
        "--template-name",
        type=str,
        help="Name of the template YAML file to create (default: 'generated.yaml')",
        default="generated.yaml",
    )
    parser.add_argument(
        "--field-mapping",
        type=str,
        help="Mapping of Anki deck fields to YAML template fields, e.g. '0:japanese,1:english'",
        required=True,
    )
    parser.add_argument(
        "--deck",
        type=str,
        help="Name of the deck to create templates for",
        required=True,
    )
    parser.add_argument(
        "apkg_file",
        type=str,
        help="Path to the existing Anki .apkg file to convert",
    )


def run(args: argparse.Namespace) -> None:
    apkg_file = Path(args.apkg_file)
    if not apkg_file.exists():
        print(f"Error: File '{apkg_file}' does not exist.")
        sys.exit(1)

    field_mapping = _parse_field_mapping(args.field_mapping)

    collection = _read_collection(apkg_file)
    print("Successfully read collection from", apkg_file)
    for deck in collection.decks:
        print(
            f"- Deck: ID={deck.id}, Name='{deck.name}' with {sum(len(notes) for notes in deck.notes.values())} notes"
        )

    deck = _get_selected_deck(args, collection)
    print(f"Selected deck: ID={deck.id}, Name='{deck.name}'")
    model_id = _get_selected_model_id(args, deck)
    notes = deck.notes[model_id]

    field_mapped_notes: list[dict[str, str]] = []
    for note in notes:
        mapped_fields: dict[str, str] = {}
        for index, field_name in field_mapping.items():
            mapped_fields[field_name] = note.fields[index]
        field_mapped_notes.append(mapped_fields)

    template_path = DECKS_PATH / args.deck / args.template_name
    cards: list[Card] = []
    template = Template(path=template_path, cards=CardCollection(vocabulary=cards))
    for note in notes:
        mapped_fields: dict[str, str] = {}
        for index, field_name in field_mapping.items():
            mapped_fields[field_name] = note.fields[index]

        card = Card(template=template, **mapped_fields)
        cards.append(card)

    save_template(template)
    print(f"Saved {len(cards)} cards to template '{template_path}'")


def _parse_field_mapping(mapping_str: str) -> dict[int, str]:
    mapping: dict[int, str] = {}
    try:
        for pair in mapping_str.split(","):
            index_str, field_name = pair.split(":")
            mapping[int(index_str)] = field_name
    except Exception:
        print("Error: Invalid field mapping format.")
        sys.exit(1)
    return mapping


def _read_collection(apkg_file: Path) -> Collection:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        shutil.unpack_archive(str(apkg_file), temp_path, format="zip")

        db_path = temp_path / "collection.anki21"
        if not db_path.exists():
            print("Error: collection.anki21 not found in the .apkg file.")
            sys.exit(1)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Read all notes from the notes table
        cursor.execute("SELECT id, mid, flds FROM notes")
        all_notes: dict[int, Note] = {}

        for note_id, model_id, fields_str in cursor.fetchall():
            # Fields are separated by the 0x1f character (ASCII 31)
            fields = fields_str.split("\x1f")
            note = Note(id=note_id, model_id=ModelId(model_id), fields=fields)
            all_notes[note_id] = note

        # Read cards table to map note_id -> deck_id
        cursor.execute("SELECT DISTINCT nid, did FROM cards")
        note_to_deck: dict[int, DeckId] = {}

        for note_id, deck_id in cursor.fetchall():
            note_to_deck[note_id] = DeckId(deck_id)

        # Read deck names from col table
        cursor.execute("SELECT decks FROM col")
        decks_json_str = cursor.fetchone()[0]
        decks_data = json.loads(decks_json_str)

        deck_names: dict[DeckId, str] = {}
        for deck_id_str, deck_info in decks_data.items():
            deck_names[DeckId(int(deck_id_str))] = deck_info["name"]

        # Group notes by deck and model
        decks_dict: dict[DeckId, dict[ModelId, list[Note]]] = {}

        for note_id, note in all_notes.items():
            if note_id not in note_to_deck:
                continue

            deck_id = note_to_deck[note_id]

            if deck_id not in decks_dict:
                decks_dict[deck_id] = {}

            if note.model_id not in decks_dict[deck_id]:
                decks_dict[deck_id][note.model_id] = []

            decks_dict[deck_id][note.model_id].append(note)

        # Construct Deck objects
        decks: list[Deck] = []
        for deck_id, notes_by_model in decks_dict.items():
            deck = Deck(
                id=deck_id, name=deck_names.get(deck_id, f"Deck {deck_id}"), notes=notes_by_model
            )
            decks.append(deck)

        conn.close()

        return Collection(decks=decks)


def _get_selected_deck(args: argparse.Namespace, collection: Collection) -> Deck:
    if args.deck_id:
        deck_id = DeckId(args.deck_id)
        deck = next((d for d in collection.decks if d.id == deck_id), None)
        if deck is None:
            print(f"No decks found for deck ID {deck_id}.")
            sys.exit(1)
        return deck

    if len(collection.decks) == 1:
        return collection.decks[0]

    print("Multiple decks found. Please specify one using --deck-id.")
    sys.exit(1)


def _get_selected_model_id(args: argparse.Namespace, deck: Deck) -> ModelId:
    if args.model_id:
        model_id = ModelId(args.model_id)
        if model_id not in deck.notes:
            print(f"No notes found for model ID {model_id}.")
            sys.exit(1)
    elif len(deck.notes) == 1:
        model_id = next(iter(deck.notes))
    else:
        print("Multiple model IDs found. Please specify one using --model-id.")
        sys.exit(1)

    return model_id
