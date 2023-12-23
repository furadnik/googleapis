"""Drive CLI."""
import webbrowser
from argparse import ArgumentParser
from pathlib import Path

from googleapis import driveapi


def upload(folder_id: str, paths: list[Path], share: bool) -> None:
    """Do the uploading."""
    folder = driveapi.get_file(folder_id)
    for path in paths:
        path = path.expanduser().absolute()
        print("Processing", path)
        if path.is_file():
            file = folder.upload(path.expanduser().resolve())
        elif path.is_dir():
            file = folder.create_folder(path.expanduser().resolve().name)
        else:
            continue
        print(file.link)
        webbrowser.open_new(file.link)
        if share:
            file.set_share(True)
        if path.is_dir():
            file.push(path.expanduser().resolve())


def add_upload_func(parser: ArgumentParser) -> None:
    """Add uploading function."""
    parser.add_argument("-f", "--folder-id", default="1_y3wMs-yZxuBtpN1TQ4GXmg2QTrbyj55")
    parser.add_argument("-s", "--share", action="store_true")
    parser.add_argument("paths", type=Path, default=[Path(".")], nargs="*")
    parser.set_defaults(func=lambda x: upload(x.folder_id, x.paths, x.share))


def add_share_func(parser: ArgumentParser) -> None:
    """Add uploading function."""
    parser.add_argument("path", type=Path)
    parser.set_defaults(func=lambda x: upload("0ByyEG1ycRwuTTGN2TXdabUZTUTQ", x.path, True))


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
