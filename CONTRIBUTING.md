# Working on the prototype

Keep documentation, diagrams, commit messages and release notes in English.

1. Install with `uv sync --extra dev` and work on a branch.
2. Change the current implementation under `src/skadis_hex`.
3. Run the snapshot tests, build the full kit, and validate the panel/jig assembly using the commands in the README.
4. Update geometry snapshots only for an intentional dimension/geometry change; describe the reason.
5. Slice the matching test set before publishing the selected current files with `python scripts/publish_current.py build/full-kit`. Update its verification records and hashes together.
6. Record physical observations with the actual filament, printer settings and tested accessory. Keep numerical checks and physical tests distinct.

Treat the archived experiments as historical records. Large numerical fields, local environments, scratch outputs and duplicate ZIP archives belong outside Git. The generated working directory is `build/`.

Preserve legacy fixtures and archived prototypes. Current panel builds must contain no legacy receiver pads or key pockets. Keep the jig flat and support-free, with the physically selected 5.2 mm locator width.

## Documentation renders

Install the optional tools with `uv sync --extra dev --extra visuals`, then run:

```sh
uv run python scripts/render_panels.py
uv run python scripts/render_kit_overview.py
uv run python scripts/publish_current.py build/full-kit
uv run python scripts/check_delivery.py
```

`render_panels.py --preview` writes smaller camera/lighting previews to ignored `work/render-preview`. Final renders use the released STL files and preserve the global lattice and nominal seam spacing.
