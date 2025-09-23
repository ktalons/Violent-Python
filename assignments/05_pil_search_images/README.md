# 05 – Image Inspection (Pillow + PrettyTable)

Goals
- Inspect files in a target directory and tabulate image properties (format, dimensions, mode).

Approach
- Validate image files using Pillow, then collect and display key attributes in a PrettyTable.

Results
- Printed table with columns: Image?, File, FileSize, Ext, Format, Width, Height, Type.

Defaults and interaction
- On launch, the script prints a default directory and prompts for input.
- If you press Enter, it uses the default: `assignments/05_pil_search_images/testImages` (when present).
- Otherwise, enter a directory path to search.

Dependencies
```bash
python3 -m pip install pillow prettytable
```

Run
```bash
python3 assignments/05_pil_search_images/05_pil_search_images.py
```
