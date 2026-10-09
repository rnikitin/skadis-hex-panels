"""Build and validate the current prototype from any checkout location."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "build",
            "validate",
            "slice",
            "screw-fit",
            "slice-screw-fit",
            "jig-fit",
            "slice-jig-fit",
            "legacy-build",
            "legacy-validate",
            "legacy-slice",
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--pilot-only",
        action="store_true",
        help="Slice only the small pilot-diameter trial",
    )
    parser.add_argument(
        "--slicer", type=Path, help="Bambu Studio executable (slicing commands)"
    )
    parser.add_argument(
        "--material",
        choices=("PLA", "PETG"),
        help="Material preset; jig trials default to PETG",
    )
    args = parser.parse_args()
    default_output = (
        "build/alignment-fit"
        if "jig-fit" in args.command
        else "build/self-tapping-fit"
        if "screw-fit" in args.command
        else "build/legacy-key"
        if args.command.startswith("legacy-")
        else "build/full-kit"
    )
    output = (args.output or Path(default_output)).resolve()
    output.mkdir(parents=True, exist_ok=True)

    if args.command == "build":
        from .kit import build

        build(output)
    elif args.command == "validate":
        from .kit import validate

        validate(output)
    elif args.command == "slice":
        from .kit_printing import slice_project

        slice_project(output, args.slicer)
    elif args.command == "jig-fit":
        from .alignment import build

        build(output)
    elif args.command == "slice-jig-fit":
        from .printing import slice_geometry_project

        material = args.material or "PETG"
        slice_geometry_project(
            output,
            "front_jig_fit_strips",
            f"front_jig_fit_strips_P2S_{material}",
            args.slicer,
            material=material,
        )
    elif args.command == "screw-fit":
        from .screw_fit import build

        build(output)
    elif args.command == "slice-screw-fit":
        from .printing import slice_geometry_project

        stem = (
            "self_tapping_3x16_pilot_test"
            if args.pilot_only
            else "self_tapping_3x16_fit"
        )
        slice_geometry_project(
            output, stem, stem + "_P2S", args.slicer, material=args.material or "PLA"
        )
    else:
        from . import joints

        joints.ROOT = output
        if args.command == "legacy-build":
            joints.build()
        elif args.command == "legacy-validate":
            from .validation import main as validate_legacy

            validate_legacy()
        else:
            from .printing import main as slice_legacy

            slice_legacy(output, args.slicer, material=args.material or "PLA")


if __name__ == "__main__":
    main()
