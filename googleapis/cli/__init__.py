"""Simple Google apis CLI."""
from argparse import ArgumentParser

from .drive import drive_parser

COMMANDS = {
    "drive": drive_parser
}


def main() -> None:
    """Run the CLI."""
    ap = ArgumentParser(description="A CLI for Google APIs.")
    subparsers = ap.add_subparsers(required=True)

    for name, func in COMMANDS.items():
        sub = subparsers.add_parser(name)
        func(sub)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
