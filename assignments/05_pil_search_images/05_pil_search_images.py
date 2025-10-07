# Kyle Versluis, 09/16/2025, Assignment 5
# Title: Identify Digital Images with PIL + Prin
"""
Purpose: Prompts for a directory, validates it,
scans files, and prints a PrettyTable with image details.
"""

import sys
from pathlib import Path

from PIL import Image               # pip install pillow
from prettytable import PrettyTable  # pip install prettytable

# Helper function to find the default directory relative to this script.
"""
Return the default directory path for test images. This function
attempts to locate the 'assets/testImages' directory relative
to the script's location, accommodating various project structures.
If the directory cannot be found, it defaults to a path based on the
script's parent directory.
"""
def repo_default_dir() -> Path:
    script = Path(__file__).resolve()

    # Attempts to find the repo root by looking for a .git folder
    for parent in [script.parent] + list(script.parents):
        repo_path = parent / "assets" / "testImages"
        if repo_path.is_dir():
            return repo_path

        # If we find a repo root marker, use it even if the folder isn't created yet
        if (parent / ".git").exists():
            return parent / "assets" / "testImages"

    # Fallback if no repo root found
    return script.parent.parent / "assets" / "testImages"

DEFAULT_DIR = repo_default_dir()

# Function to format integers with thousands of separators
def format_int(n: int) -> str:
    try:
        return f"{int(n):,}"
    except Exception:
        return str(n)

# Function to inspect if a file is an image and get its properties
# Returns: (is_image, img_format, width, height, mode) which fits in prettytable
# If not an image, returns (False, None, None, None, None)
def inspect_image(path: Path):
    try:
        with Image.open(path) as im:
            im.verify()  # validate file is an image
        with Image.open(path) as im2:
            fmt = im2.format
            w, h = im2.size
            mode = im2.mode
        return True, fmt, w, h, mode
    except Exception:
        return False, None, None, None, None


def build_table() -> PrettyTable:
    t = PrettyTable()
    t.field_names = ["Image?", "File", "FileSize", "Ext", "Format", "Width", "Height", "Type"]
    t.align["Image?"] = "l"
    t.align["File"] = "l"
    t.align["FileSize"] = "r"
    t.align["Ext"] = "l"
    t.align["Format"] = "l"
    t.align["Width"] = "r"
    t.align["Height"] = "r"
    t.align["Type"] = "l"
    return t


def main() -> None:
    print(f"Press enter to inspect the image files in listed directory below...\n  {DEFAULT_DIR}")
    print("Otherwise, enter another directory path to search instead.")
    user_input = input("Directory path: ").strip()
    dir_path = Path(user_input) if user_input else Path(DEFAULT_DIR)
    dir_path = dir_path.expanduser().resolve()

    if not dir_path.exists() or not dir_path.is_dir():
        print(f"ERROR: '{dir_path}' is not a valid directory.")
        sys.exit(1)

    table = build_table()

    for entry in sorted(dir_path.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_file():
            continue

        is_img, fmt, w, h, mode = inspect_image(entry)
        size_bytes = entry.stat().st_size
        table.add_row([
            "YES" if is_img else "NO",
            str(entry),
            format_int(size_bytes),
            entry.suffix.lower() if entry.suffix else "",
            fmt or "",
            w or "",
            h or "",
            mode or "",
        ])

    print(table)


if __name__ == "__main__":
    main()
