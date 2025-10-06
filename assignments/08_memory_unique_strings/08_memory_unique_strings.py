# Kyle Versluis, 09/30/2025, Assignment 8
# Title: Memory Dump Unique Strings Extractor
# Purpose: Process a memory dump to identify unique alphabetical strings and
# report their occurrence counts in a PrettyTable sorted by the highest count.

# Notes:
# - Reads the file in chunks with an overlap window so matches that span chunk
#   boundaries are captured. For this pattern, a max length of 15, an overlap of 14
#   bytes is enough and used by default.
# - Requires the prettytable package for tabular output
"""
- Requires Python 3.6+
- 3rd party dependencies: prettytable
pip install prettytable

Usage:
  python3 process_memory_strings.py /path/to/memdump.bin [--chunk-size BYTES] [--overlap BYTES]
"""

import argparse                                 # For command-line parsing
import re                                       # For regular expression matching
import sys                                      # For exit codes
from typing import Dict, Iterable, Tuple        # For type hints
from prettytable import PrettyTable             # For formatted table output
from pathlib import Path

# Default streaming parameters
DEFAULT_CHUNK_SIZE = 1024 * 1024                # 1 MiB
DEFAULT_OVERLAP = 14                            # because the max token length is 15

# Helper function to find the default directory relative to this script.
"""
Return the default directory path for test images. This function
attempts to locate the 'assets/test.bin' directory relative
to the script's location, accommodating various project structures.
If the directory cannot be found, it defaults to the current working directory.
"""
def repo_default_dir() -> Path:
    script = Path(__file__).resolve()

    # Attempts to find the repo root by looking for a .git folder
    for parent in script.parents:
        repo_path = parent / "assets" / "test.bin"
        if repo_path.is_dir():
            return repo_path

        # If we find a repo root marker, use it even if the folder isn't created yet
        if (parent / ".git").exists():
            return parent / "assets" / "test.bin"

    # Fallback if no repo root found
    return Path.cwd()

DEFAULT_DIR = repo_default_dir()
print(f"[info] Using default directory: {DEFAULT_DIR}")


# Word regex: continuous alphabetical strings 5-15 chars long
wPatt = re.compile(rb'[A-Za-z]{5,15}')

# Helper functions
# ----------------------------------------------------------------------------------------------

# Count matches in the given bytes region and update counts dict
def matchCount(region: bytes, counts: Dict[bytes, int]) -> None:
    """Update counts with matches found within the given bytes region."""
    for m in wPatt.findall(region):
        counts[m] = counts.get(m, 0) + 1

# Scan a binary file for the word pattern using chunked reads with overlap and update counts dict.
def wordScan(path: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> Dict[bytes, int]:
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    # Initialize counts dict
    counts: Dict[bytes, int] = {}

    # try to open the file and read in chunks
    try:
        with open(path, 'rb') as f:
            buffer = b''

            # read in chunks, looping until EOF and records matches
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    # Process whatever remains in the buffer
                    if buffer:
                        matchCount(buffer, counts)
                    break

                buffer += chunk

                # Process the buffer if it exceeds the overlap size and retain overlap
                if len(buffer) > overlap:
                    scan_region = buffer[:-overlap]
                    buffer = buffer[-overlap:]
                    matchCount(scan_region, counts)
    # handle errors
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except PermissionError:
        print(f"Error: permission denied: {path}", file=sys.stderr)
        sys.exit(2)

    return counts

# Convert counts dict to rows sorted by count desc then string asc (case-insensitive).
def countToSortedrow(counts: Dict[bytes, int]) -> Iterable[Tuple[str, int]]:
    # decodes bytes to string, replacing invalid characters with '?'
    def byte2string(b: bytes) -> str:
        return b.decode('ascii')

    return sorted(((byte2string(k), v) for k, v in counts.items()), key=lambda kv: (-kv[1], kv[0].lower()))
# ------------------------------------------------------------------------------------------------------

# Main function: parse command-line arguments and run the scan
def main() -> int:
    ap = argparse.ArgumentParser(description="Extract 5–15 letter strings and show hit counts in a PrettyTable")
    ap.add_argument('dump', default={DEFAULT_DIR}, help='Path to memory dump (binary file)')
    ap.add_argument('--chunk-size', type=int, default=DEFAULT_CHUNK_SIZE, help=f'Chunk size in bytes (default: {DEFAULT_CHUNK_SIZE})')
    ap.add_argument('--overlap', type=int, default=DEFAULT_OVERLAP, help=f'Overlap window in bytes (default: {DEFAULT_OVERLAP})')

    args = ap.parse_args()

    # scan the file and get results
    counts = wordScan(args.dump, args.chunk_size, args.overlap)

    # PrettyTable is optional at import-time, so we can give a clear error if missing
    try:
        from prettytable import PrettyTable
    except Exception as e:
        print("Error: prettytable is required for formatted output. Install with:", file=sys.stderr)
        print("  python3 -m pip install prettytable", file=sys.stderr)
        return 3

    # print results in a PrettyTable
    table = PrettyTable()
    table.field_names = ["String", "Occurrences"]
    table.align["String"] = "l"
    table.align["Occurrences"] = "r"

    for s, c in countToSortedrow(counts):
        table.add_row([s, c])

    print(table)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
