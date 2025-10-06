# Kyle Versluis, 09/27/2025, Assignment 7
# Title: Extracting Indicators from Memory Dumps
# Purpose: Extracts e-mail addresses and URLs from a memory dump in chunked binary reads.

# Notes: Uses regular expressions to find e-mail addresses and URLs. Report unique values
# and optionally shows occurrence counts.
"""
Requires Python 3.6+
3rd party dependencies:
pip install prettytable

Usage:
  python3 extract_indicators.py /path/to/memdump.bin [--chunk-size BYTES] [--overlap BYTES] /
  [--json-out out.json] [--show-counts]
"""
import argparse                         # For command-line parsing
import json                             # For JSON output
import re                               # For regular expression matching
import sys                              # For exit codes
from typing import Dict, Set, Tuple     # For type hints
from pathlib import Path                # For path manipulations

# Default I/O parameters
DEFAULT_CHUNK_SIZE = 1024 * 1024        # 1 MiB
DEFAULT_OVERLAP = 2048                  # bytes kept between chunks to catch boundary-spanning matches


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
# ----------------------------------------------------------------------------------------------

# Regular expressions for e-mails and URLs. ePatt and uPatt are compiled once.
# ePatt: e-mail addresses and URLs
ePatt = re.compile(rb'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}')
uPatt = re.compile(rb'\w+:\/\/[\w@][\w.:@]+\/?[\w\.?=%&=\-@$,]*')

# Helper functions
# ----------------------------------------------------------------------------------------------
# decodes bytes to string, replacing invalid characters with '?'
def byte2string(b: bytes) -> str:
    return b.decode('utf-8', errors='replace')

# scans a binary file for emails and URLs using chunked reads with overlap
def fileScan(path: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP
             ) -> Tuple[Dict[bytes, int], Dict[bytes, int], Set[bytes], Set[bytes]]:
    if overlap < 0:
        raise ValueError("overlap must be >= 0")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    # Initialize counts and sets
    email_counts: Dict[bytes, int] = {}
    url_counts: Dict[bytes, int] = {}
    email_set: Set[bytes] = set()
    url_set: Set[bytes] = set()

    # try to open the file and read in chunks
    try:
        with open(path, 'rb') as f:
            buffer = b''
            # read in chunks, looping until EOF and records matches
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    scan_region = buffer
                    if scan_region:
                        for match in ePatt.findall(scan_region):
                            email_set.add(match)
                            email_counts[match] = email_counts.get(match, 0) + 1
                        for match in uPatt.findall(scan_region):
                            url_set.add(match)
                            url_counts[match] = url_counts.get(match, 0) + 1
                    break

                buffer += chunk

                # Process the buffer if it exceeds the overlap size and retain overlap
                if len(buffer) > overlap:
                    scan_region = buffer[:-overlap]
                    buffer = buffer[-overlap:]

                    # Find matches in the scan region and add to sets
                    for match in ePatt.findall(scan_region):
                        email_set.add(match)
                        email_counts[match] = email_counts.get(match, 0) + 1
                    for match in uPatt.findall(scan_region):
                        url_set.add(match)
                        url_counts[match] = url_counts.get(match, 0) + 1
    # handle errors
    except FileNotFoundError:
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except PermissionError:
        print(f"Error: permission denied: {path}", file=sys.stderr)
        sys.exit(2)

    return email_counts, url_counts, email_set, url_set

# converts a set of bytes to a sorted list of strings
def sortedStrings(items: Set[bytes]) -> list:
    return sorted((byte2string(x) for x in items), key=lambda s: (s.lower(), s))

# converts a counts dict to a sorted list of tuples (string, count)
def countsSortedStrings(counts: Dict[bytes, int]) -> list:
    return sorted(((byte2string(k), v) for k, v in counts.items()), key=lambda kv: (-kv[1], kv[0].lower()))
# ----------------------------------------------------------------------------------------------

# Main function: parse command-line arguments and run the scan
def main() -> int:
    ap = argparse.ArgumentParser(description="Extract e-mails and URLs from a memory dump (binary-safe)")
    ap.add_argument('dump', default={DEFAULT_DIR}, help='Path to memory dump (binary file)')
    ap.add_argument('--chunk-size', type=int, default=DEFAULT_CHUNK_SIZE, help=f'Chunk size for reading (default: {DEFAULT_CHUNK_SIZE})')
    ap.add_argument('--overlap', type=int, default=DEFAULT_OVERLAP, help=f'Overlap window between chunks (default: {DEFAULT_OVERLAP})')
    ap.add_argument('--json-out', type=str, default=None, help='Optional path to write results as JSON')
    ap.add_argument('--show-counts', action='store_true', help='Show occurrence counts per unique value')

    args = ap.parse_args()                         # Parse command-line arguments

    # Scan the file and get results
    email_counts, url_counts, email_set, url_set = fileScan(args.dump, args.chunk_size, args.overlap)

    emails_sorted = sortedStrings(email_set)       # Convert sets to sorted lists
    urls_sorted = sortedStrings(url_set)

    print(f"Unique emails: {len(emails_sorted)}")
    print(f"Unique URLs:   {len(urls_sorted)}")

    # display counts if requested
    if args.show_counts:
        print("\nTop e-mail occurrences:")
        for email, cnt in countsSortedStrings(email_counts)[:50]:
            print(f"{cnt:6d}  {email}")
        print("\nTop URL occurrences:")
        for url, cnt in countsSortedStrings(url_counts)[:50]:
            print(f"{cnt:6d}  {url}")

    print("\nAll e-mails:")
    for s in emails_sorted:
        print(s)

    print("\nAll URLs:")
    for s in urls_sorted:
        print(s)

    # Offer to save results as JSON if requested
    if args.json_out:
        result = {
            'emails': emails_sorted,
            'urls': urls_sorted,
        }
        # write JSON output
        try:
            with open(args.json_out, 'w', encoding='utf-8') as out:
                json.dump(result, out, indent=2, ensure_ascii=False)
            print(f"\nWrote JSON results to {args.json_out}")
        except Exception as e:
            print(f"Failed to write JSON output: {e}", file=sys.stderr)
            return 3

    return 0


if __name__ == '__main__':
    raise SystemExit(main())