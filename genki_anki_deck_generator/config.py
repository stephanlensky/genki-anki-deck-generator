import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

CONFIG_PATH = Path("config/config.toml")
DECKS_PATH = Path("config/decks")


@dataclass(kw_only=True)
class ConfigSources:
    audio: dict[str, str]
    fonts: str


@dataclass(kw_only=True)
class Config:
    decks: dict[str, str]
    deck_ids: dict[str, int]
    download_dir: Path
    sources: ConfigSources
    dedupe: bool = True


@dataclass(kw_only=True)
class DeckAudioFileOverride:
    fuse_with_next: int | None = None
    resplit: int | None = None


@dataclass(kw_only=True)
class DeckAudioFile:
    sound_file: Path
    sound_silence_threshold: int
    overrides: dict[int, DeckAudioFileOverride] | None = None


@dataclass(kw_only=True)
class DeckConfig:
    audio: list[DeckAudioFile]
    templates: list[Path]


@cache
def get_config() -> Config:
    with open(CONFIG_PATH, "rb") as f:
        config_dict = tomllib.load(f)

    config = Config(
        decks=config_dict["settings"]["decks"],
        deck_ids=config_dict["settings"]["deck_ids"],
        download_dir=Path(config_dict["settings"]["download_dir"]),
        sources=ConfigSources(
            audio=config_dict["settings"]["sources"]["audio"],
            fonts=config_dict["settings"]["sources"]["fonts"],
        ),
        dedupe=config_dict["settings"].get("dedupe", False),
    )

    assert all(deck in config.deck_ids for deck in config.decks), (
        "All decks in the configuration must have a corresponding ID in deck_ids."
    )
    return config


@cache
def get_deck_config(deck_name: str) -> DeckConfig:
    deck_config_path = DECKS_PATH / deck_name
    audio_config = deck_config_path / "audio.yaml"

    templates = list(deck_config_path.glob("**/*.yaml"))
    templates.remove(audio_config)

    with open(audio_config, "r") as f:
        audio_dict = yaml.safe_load(f)

    return DeckConfig(
        audio=[
            DeckAudioFile(
                sound_file=Path(item["sound_file"]),
                sound_silence_threshold=item["sound_silence_threshold"],
                overrides={
                    int(k): DeckAudioFileOverride(**v) for k, v in item.get("overrides", {}).items()
                }
                or None,
            )
            for item in audio_dict["audio"]
        ],
        templates=templates,
    )


def set_config_path(path: Path) -> None:
    global CONFIG_PATH
    CONFIG_PATH = path
    get_config.cache_clear()


def set_decks_path(path: Path) -> None:
    global DECKS_PATH
    DECKS_PATH = path
    get_deck_config.cache_clear()
