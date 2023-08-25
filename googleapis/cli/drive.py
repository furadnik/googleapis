"""Drive CLI."""
import webbrowser
from argparse import ArgumentParser
from pathlib import Path

from googleapis import driveapi


def upload(folder_id: str, path: Path) -> None:
    """Do the uploading."""
    folder = driveapi.get_file(folder_id)
    if path.is_file():
        file = folder.upload(path.expanduser().resolve())
        print(file.link)
        webbrowser.open_new(file.link)
    elif path.is_dir():
        file = folder.create_folder(path.expanduser().resolve().name)
        print(file.link)
        webbrowser.open_new(file.link)
        file.push(path.expanduser().resolve())


def add_upload_func(parser: ArgumentParser) -> None:
    """Add uploading function."""
    parser.add_argument("--path", type=Path, default=".")
    parser.add_argument("--folder-id", default="1_y3wMs-yZxuBtpN1TQ4GXmg2QTrbyj55")
    parser.set_defaults(func=lambda x: upload(x.folder_id, x.path))


def add_share_func(parser: ArgumentParser) -> None:
    """Add uploading function."""
    parser.add_argument("path", type=Path)
    parser.set_defaults(func=lambda x: upload("0ByyEG1ycRwuTTGN2TXdabUZTUTQ", x.path))


DRIVE_SUBCOMMANDS = {
    "upload": add_upload_func,
    "share": add_share_func
}


def drive_parser(parser: ArgumentParser) -> None:
    """Add drive subcommands."""
    subcommands = parser.add_subparsers(required=True)
    for name, adder in DRIVE_SUBCOMMANDS.items():
        sub = subcommands.add_parser(name)
        adder(sub)
