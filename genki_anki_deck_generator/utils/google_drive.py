import zipfile
from pathlib import Path

import gdown


def google_drive_download(file_id: str, destination: Path, unzip: bool = False) -> None:
    """Download a file from Google Drive."""
    if not unzip:
        destination.parent.mkdir(parents=True, exist_ok=True)
        gdown.download(id=file_id, output=str(destination))
        print(f"Downloaded {destination} from Google Drive.")
        return

    destination.mkdir(parents=True, exist_ok=True)
    zip_destination = destination / f"{destination.stem}.zip"
    gdown.download(id=file_id, output=str(zip_destination))
    with zipfile.ZipFile(zip_destination, "r") as zip_ref:
        zip_ref.extractall(destination)
    print(f"Unzipped {zip_destination} to {destination}")
    zip_destination.unlink()
