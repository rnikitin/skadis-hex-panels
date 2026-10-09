"""Build and validate the current prototype from any checkout location."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("build", "validate", "slice", "screw-fit", "slice-screw-fit"),
    )
    parser.add_argument("--output", type=Path, default=Path("build/current"))
    parser.add_argument(
        "--pilot-only",
        action="store_true",
        help="Slice only the small pilot-diameter trial",
    )
    parser.add_argument(
        "--slicer", type=Path, help="Bambu Studio executable (slicing commands)"
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    from . import joints

    joints.ROOT = output
    if args.command == "screw-fit":
        from .screw_fit import build

        build(output)
    elif args.command == "slice-screw-fit":
        from .printing import slice_geometry_project

        stem = (
            "self_tapping_3x16_pilot_test"
            if args.pilot_only
            else "self_tapping_3x16_fit"
        )
        slice_geometry_project(output, stem, stem + "_P2S", args.slicer)
    elif args.command == "build":
        joints.build()
    elif args.command == "validate":
        from .validation import main as validate

        validate()
    else:
        from .printing import main as slice_project

        slice_project(output, args.slicer)


if __name__ == "__main__":
    main()
