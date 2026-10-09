# Project operating notes

- Use one material per native project with the installed Bambu Studio 02.08.02.61 CLI. A four-plate run with PLA in filament slot 1 and PETG in slot 2 crashes in nozzle-group lookup; `kit_printing.py` produces the all-PETG kit and a separate PLA panel. Each material is mapped to the single P2S extruder.
- Bambu Studio can save over an opened 3MF and remove cached toolpaths or change its settings. Before publishing a saved project, validate the embedded G-code, material, object counts and supports, then refresh the manifest. Preserve locally saved variants before restoring historical generated files.
- The accepted jig locator width is 5.2 mm from a PETG strip. Current depth is 4.4 mm; the body is flat and support-free. Increased depth/full four-point fit remains a full-kit physical test, not part of the already reported strip result.
