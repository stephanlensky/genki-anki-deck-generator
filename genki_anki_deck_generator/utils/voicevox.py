from dataclasses import dataclass
from typing import Any, Literal

import requests

VOICEVOX_API = "http://127.0.0.1:50021"


@dataclass
class VoiceVoxSpeakerStyle:
    name: str
    id: int
    type: str


@dataclass
class VoiceVoxSpeaker:
    name: str
    speaker_uuid: str
    styles: list[VoiceVoxSpeakerStyle]


def get_speakers() -> list[VoiceVoxSpeaker]:
    response = _request("GET", "/speakers")
    speakers_data = response.json()
    speakers = []
    for speaker in speakers_data:
        styles = [
            VoiceVoxSpeakerStyle(name=style["name"], id=style["id"], type=style["style_type"])
            for style in speaker["styles"]
        ]
        speakers.append(
            VoiceVoxSpeaker(
                name=speaker["name"], speaker_uuid=speaker["speaker_uuid"], styles=styles
            )
        )
    return speakers


def _request(method: Literal["GET", "POST"], endpoint: str, **kwargs: Any) -> requests.Response:
    url = f"{VOICEVOX_API}/{endpoint.lstrip('/')}"
    response = requests.request(method, url, **kwargs)
    response.raise_for_status()
    return response
