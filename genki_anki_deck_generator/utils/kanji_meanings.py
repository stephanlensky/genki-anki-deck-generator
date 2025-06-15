import json
from pathlib import Path
from typing import Any

import requests

from genki_anki_deck_generator.config import get_config

KANJI_DATA_PATH = Path("kanji-wanikani.json")
_KANJI_DATA: dict[str, Any] | None = None


def get_kanji_meanings(kanji: str) -> list[str] | None:
    """
    Get the meaning of a kanji character from the kanji data file.
    Returns None if the kanji is not found.
    """
    global _KANJI_DATA
    if _KANJI_DATA is None:
        config = get_config()
        kanji_data_path = config.download_dir / KANJI_DATA_PATH
        if not kanji_data_path.exists():
            raise FileNotFoundError(f"Kanji data file not found at {kanji_data_path}")

        with kanji_data_path.open("r", encoding="utf-8") as f:
            _KANJI_DATA = json.load(f)

    return _KANJI_DATA.get(kanji, {}).get("wk_meanings")  # type: ignore


def download_kanji_data(overwrite: bool = False) -> None:
    config = get_config()
    kanji_data_path = config.download_dir / KANJI_DATA_PATH
    if not kanji_data_path.exists() or overwrite:
        answer = requests.get(
            "https://raw.githubusercontent.com/davidluzgouveia/kanji-data/master/kanji-wanikani.json"
        )
        parsed = json.loads(answer.text)
        with kanji_data_path.open("w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
    else:
        print(f"Skipping download of kanji data, already exists at {kanji_data_path}")
