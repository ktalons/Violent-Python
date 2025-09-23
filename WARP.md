# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository overview

This repository contains a Python 3.11+ portfolio of small, self-contained cybersecurity scripts and a simple Tkinter GUI (“Showcase”) to browse and run them. The code is organized as standalone assignments with minimal shared infrastructure. There is no test suite, build system, or linter configuration in the repo.

Sources referenced:
- README.md (project description, GUI usage, Python version badge)
- main.py, start.sh, start.ps1 (GUI launcher and helpers)
- requirements*.txt (Python package dependencies)
- assignments/*/*.py (script contents)
- .github/workflows/close-prs.yml (PR policy)

## Commands you’ll commonly use

- Launch the GUI (recommended for browsing scripts)
  - macOS/Linux
    - ./start.sh
  - Windows (PowerShell)
    - ./start.ps1
  - Alternatively (any OS, after creating a venv):
    - python main.py

- Run a specific assignment script from the repo root
  - 01 – String search
    - python3 assignments/01_string_search/01_string_search.py
  - 02 – Firewall log parser (expects a file named redhat.txt in the current directory)
    - python3 assignments/02_firewall_parser/02_firewall_parser.py
  - 03 – Hashing forensics
    - Defaults to scanning the testImages folder next to the script.
    - To choose a directory: add -d /path/to/dir
    - python3 assignments/03_hashing_forensics/03_hashing_forensics.py [-d <dir>]
  - 04 – File processor (interactive; prompts for a directory)
    - python3 assignments/04_file_processor_oop/04_file_processor_oop.py
  - 05 – Image inspection (Pillow + PrettyTable)
    - Defaults to assignments/05_pil_search_images/testImages if present; otherwise prompts for a directory.
    - Install dependencies first (see below), then:
    - python3 assignments/05_pil_search_images/05_pil_search_images.py

- Optional: create and use a virtual environment
  - python3 -m venv .venv
  - source .venv/bin/activate
  - python -m pip install --upgrade pip

- Dependencies
  - This repo includes requirements.txt with:
    - pillow
    - prettytable
  - OS-specific variants are provided: requirements-macos.txt, requirements-linux.txt, requirements-windows.txt.
  - Not all scripts need these packages; Assignment 05 does. The GUI can run without Pillow but won’t animate GIFs.

- Linting: Not configured in this repo (no flake8/ruff/black config files found)
- Tests: No test suite or runner present
- Build: Not applicable (pure Python scripts)

## High-level architecture and structure

- GUI and launchers
  - main.py — Tkinter GUI (“Showcase”) to preview and run assignments
  - start.sh / start.ps1 — create a venv, upgrade pip, install requirements.txt if present, and launch the GUI
  - .vp_showcase_prefs.json — small JSON preferences file (created at first run)

- assignments/
  - 00_showcase_check/
    - show_env.py — prints environment details (non-sensitive)
    - showcase.py — small demo that prints progress lines
  - 01_string_search/
    - Demonstrates basic string normalization, counting, sorting, and substring search against a fixed excerpt.
  - 02_firewall_parser/
    - Reads a local log file named redhat.txt (from the current working directory), extracts case-insensitive tokens containing "worm", and prints a sorted unique list. Uses only the Python standard library.
    - A sample redhat.txt is included under assets/week1/, and another copy exists at the repo root.
  - 03_hashing_forensics/
    - Computes MD5 hashes for files. By default scans the testImages folder next to the script; use -d to target another directory.
  - 04_file_processor_oop/
    - Interactive script using a FileProcessor class to collect basic file metadata (size, times, mode, UID) and the first 20 bytes of the header (hexlified), then pretty-prints per file in a user-provided directory.
  - 05_pil_search_images/
    - Interactive script to inspect files in a target directory and tabulate image properties (format, dimensions, mode). Requires third-party libs: Pillow and PrettyTable.
    - Uses assignments/05_pil_search_images/testImages as the default when present; otherwise prompts for a directory.
  - 06+ directories are placeholders for future assignments unless scripts are added.

- assets/
  - week1/
    - Contains redhat.txt (sample log for assignment 02) and references used in early coursework.
  - python-logo.png (used by the GUI splash; logo.gif/logo.png are also supported if present)

- .github/workflows/close-prs.yml
  - CI job that automatically comments on and closes opened/reopened pull requests. This repo doesn’t accept PRs; fork to propose changes.

## Notes for Warp

- Operate with Python 3.11+.
- A central requirements.txt exists (pillow, prettytable). OS-specific variants are available.
- Some scripts operate on the current working directory; prefer running them from an intended data directory to avoid scanning/hashing large trees.
- When using Git in this repo, prefer no-pager options to avoid interactive pagers (e.g., git --no-pager log).
- No CLAUDE, Cursor, or Copilot rule files were found in this repository.
