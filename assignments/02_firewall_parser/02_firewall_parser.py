# Kyle Versluis, 09/07/2025, Assignment 2
# Title: Simple File Processing
# Purpose: Extracts and displays a sorted list of tokens containing "worm" from a log file

# Import Python Standard Libraries
from pathlib import Path
import sys


def main() -> int:
    # Allow optional filename argument; default to "redhat.txt" in the current working directory
    filename = sys.argv[1] if len(sys.argv) > 1 else "redhat.txt"
    path = Path(filename)

    if not path.exists() or not path.is_file():
        try:
            attempted = str(path.resolve())
        except Exception:
            attempted = str(path)
        print(f"Error: file not found -> {attempted}")
        print("Tip: Place redhat.txt in the current working directory or pass a path:\n"
              "  python3 assignments/02_firewall_parser/02_firewall_parser.py /path/to/redhat.txt")
        return 1

    unique_worms: set[str] = set()

    try:
        with path.open('r', encoding='utf-8', errors='ignore') as log_file:
            for each_line in log_file:
                for token in each_line.split():
                    if "worm" in token.lower():
                        unique_worms.add(token)
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return 1

    # Case-insensitive sort for friendlier output while preserving original token case
    for token in sorted(unique_worms, key=lambda s: s.lower()):
        print(token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
