import asyncio
from pathlib import Path

from voicevox import Client


def voicevox_tts(text: str, speaker: int, output_path: Path) -> None:
    asyncio.run(_voicevox_tts(text, speaker, output_path))


async def _voicevox_tts(text: str, speaker: int, output_path: Path) -> None:
    async with Client() as client:
        audio_query = await client.create_audio_query(text, speaker=speaker)
        with open(output_path, "wb") as f:
            f.write(await audio_query.synthesis(speaker=speaker))
