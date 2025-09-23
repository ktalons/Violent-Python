# Kyle Versluis, 09/07/2025, Assignment 3
# Title: File Hashing
# Purpose: Creates a dictionary of file hashes from files under a target directory.
# By default, targets the testImages folder next to this script to avoid hashing large trees.

# Imports
import os
import sys
import argparse
import hashlib


def resolve_target_directory(cli_dir: str | None) -> str:
    """
    Resolve the directory to scan:
    - If provided via CLI, use that.
    - Else, use ./testImages relative to this script if it exists.
    - Else, fall back to current working directory.
    """
    if cli_dir:
        return cli_dir

    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_dir = os.path.join(script_dir, "testImages")
    if os.path.isdir(default_dir):
        return default_dir

    return "."


def collect_files(root_dir: str) -> list[str]:
    """Walk the directory tree and collect absolute file paths."""
    files: list[str] = []
    for root, _dirs, filenames in os.walk(root_dir):
        for name in filenames:
            path = os.path.join(root, name)
            files.append(os.path.abspath(path))
    return files


def md5_hash_file(path: str) -> str | None:
    """Return the MD5 hex digest for a file, or None if unreadable."""
    try:
        with open(path, "rb") as fh:
            return hashlib.md5(fh.read()).hexdigest()
    except (PermissionError, IsADirectoryError, FileNotFoundError, OSError):
        print(f"Skipping unreadable file: {path}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute MD5 hashes for files under a directory."
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="directory",
        help=(
            "Directory to scan (defaults to 'testImages' next to this script if present, "
            "otherwise '.' (current working directory))."
        ),
    )
    args = parser.parse_args()

    directory = resolve_target_directory(args.directory)

    # Build the hash dictionary: {hash: path}
    file_hashes: dict[str, str] = {}
    for file_path in collect_files(directory):
        digest = md5_hash_file(file_path)
        if digest is not None:
            file_hashes[digest] = file_path

    # Print key, value pairs
    for key, value in file_hashes.items():
        print(key, value)


if __name__ == "__main__":
    main()
