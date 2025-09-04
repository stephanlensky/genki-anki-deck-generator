import subprocess
from pathlib import Path


def voicepeak_tts(text: str, narrator: str, output_path: Path) -> None:
    command = [
        "voicepeak",
        "-n",
        narrator,
        "--say",
        text,
        "--out",
        str(output_path),
    ]
    print(" ".join(command))
    process = subprocess.Popen(command)
    try:
        return_code = process.wait(timeout=10)
        if return_code != 0:
            raise RuntimeError("Voicepeak TTS generation failed.")
    except TimeoutError:
        process.terminate()
        print("Error: Voicepeak TTS generation timed out.")
        raise

    if not output_path.exists():
        raise RuntimeError("Voicepeak TTS generation failed, output file not created.")
