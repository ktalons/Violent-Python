#!/usr/bin/env python3
import os
import sys
import platform
from pathlib import Path

def main():
    print("Environment overview (non-sensitive)")
    print(f"Python: {sys.version.split()[0]} on {platform.system()} {platform.release()}")
    print(f"Executable: {sys.executable}")
    print(f"CWD: {Path.cwd()}")
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        print(f"Virtualenv: {venv}")
    else:
        print("Virtualenv: (none)")
    names = sorted(os.environ.keys())
    print(f"Env vars ({len(names)}):")
    for name in names:
        print(f" - {name}")

if __name__ == "__main__":
    main()
