"""Build and validate the current prototype from any checkout location."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "validate", "slice"))
    parser.add_argument("--output", type=Path, default=Path("build/current"))
    parser.add_argument(
        "--slicer", type=Path, help="Bambu Studio executable (slice only)"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    from . import joints

    joints.ROOT = output
    if args.command == "build":
        joints.build()
    elif args.command == "validate":
        from .validation import main as validate

        validate()
    else:
        from .printing import main as slice_project

        slice_project(output, args.slicer)


if __name__ == "__main__":
    main()
