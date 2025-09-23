# 🐍 Violent Python: Script Portfolio

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](#)
[![Course](https://img.shields.io/badge/Course-CYBV%20473-%23CC0033)](#)
[![Status](https://img.shields.io/badge/Status-Active-green)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A curated collection of scripting assignments demonstrating practical Python for cybersecurity coursework. Includes a Tkinter GUI to browse and run scripts.

> Educational use only. Do not use these scripts to violate policies or laws.

---

## 🚀 Quick start

- macOS/Linux (recommended):
  ```bash
  ./start.sh
  ```
- Windows (PowerShell):
  ```powershell
  ./start.ps1
  ```
- Manual (any OS):
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  python main.py
  ```

Notes
- The Setup screen can preview and install OS-specific requirement files (requirements-<os>.txt).
- The Showcase screen auto-discovers `*.py` under `./assignments/*/`, previews code, and runs a selected script.
- Splash image: prefers `assets/logo.gif` (animated when Pillow is installed), then `assets/python-logo.png`.

---

## 📦 Dependencies

This repo is mostly standard-library Python; a few scripts use third-party packages:
- Pillow (optional) for images/splash animation
- PrettyTable for tabular CLI output (Assignment 05)

OS-specific requirement files are provided:
- requirements-macos.txt
- requirements-linux.txt
- requirements-windows.txt

The generic requirements.txt is intentionally minimal. Use the OS-specific files via the GUI or install the two packages above when needed.

---

## 🗂️ Repository structure

```
Violent-Python/
├─ main.py                     # Tkinter GUI to run/preview assignments
├─ start.sh                    # macOS/Linux launcher (creates .venv, checks Tk)
├─ start.ps1                   # Windows launcher (creates .venv, checks Tk)
├─ assignments/
│  ├─ 00_showcase_check/        # GUI pre-flight checks and helpers
│  │  ├─ show_env.py           # Prints Python/Tk/Pillow availability and versions
│  │  └─ showcase.py           # Minimal sample to validate GUI runner via terminal
│  ├─ 01_string_search/
│  ├─ 02_firewall_parser/
│  ├─ 03_hashing_forensics/
│  ├─ 04_file_processor_oop/
│  ├─ 05_pil_search_images/
│  ├─ 06_exif_geotag_extractor/
│  ├─ 07_memory_regex_extract/
│  ├─ 08_memory_unique_strings/
│  ├─ 09_web_crawler_scraper/
│  ├─ 10_tcp_server/
│  ├─ 11_tcp_client/
│  ├─ 12_packet_sniffer/
│  ├─ 13_pcap_asset_mapping/
│  ├─ 14_lsb_steganography/
│  ├─ 15_hashtag_collector/
│  ├─ 16_social_graph_harvest/
│  ├─ 17_nltk_transcript_analysis/
│  ├─ 18_mp3_id3_carver/
│  ├─ 19_virustotal_client/
│  └─ 20_tbd/
├─ assets/
│  ├─ python-logo.png
│  ├─ screenshots/
│  │  ├─ splash.png            # add your screenshot
│  │  ├─ setup.png             # add your screenshot
│  │  └─ showcase.png          # add your screenshot
│  └─ week1/
│     ├─ README.md
│     └─ redhat.txt            # sample log referenced by assignment 02
├─ requirements.txt
├─ requirements-macos.txt
├─ requirements-linux.txt
├─ requirements-windows.txt
├─ .github/workflows/close-prs.yml
├─ LICENSE
├─ README.md
└─ WARP.md
```

---

## 🖥️ GUI Showcase (Tkinter)

The desktop app lets you:
- Install/preview OS-specific requirements
- Install (single click): sets up the preferred terminal for your selected OS and runs `pip install -r` on the displayed `requirements-<os>.txt`
- Discover `./assignments/*/*.py` automatically
- Preview syntax-highlighted code
- Run a selected script in your preferred terminal

The GUI stores a small JSON preferences file at `.vp_showcase_prefs.json` for terminal selection and first-run notices.

---

## 🧹 Safe Uninstall

The Uninstall button in the Setup screen now performs a safe uninstall across macOS, Linux, and Windows:

- Two-step confirmation: you must type the exact project folder name to proceed.
- Prefers moving the project folder to the OS Trash/Recycle Bin:
  - macOS: uses Finder to move the folder to Trash.
  - Windows: uses the Recycle Bin API.
  - Linux: uses gio trash when available.
- If Trash/Recycle Bin is unavailable, it falls back to a non-destructive safe rename: <folder>.DELETE_ME_YYYYmmdd_HHMMSS (nothing is permanently deleted).
- Strong safety checks ensure the operation only targets this repo (looks for markers like main.py and README.md; refuses root/home/very-short paths).
- It never modifies system tools or packages (Python, Homebrew, winget, etc.).

Recovery and final cleanup:
- If moved to Trash/Recycle Bin, restore or empty your Trash as desired.
- If safely renamed, you can manually inspect and delete the renamed folder when ready.

### Smoke test: Safe Uninstall

Run the cross-platform smoke test without touching your repo:
- macOS/Linux:
  ```bash
  python3 scripts/e2e_uninstall_smoke.py
  ```
- Windows (PowerShell):
  ```powershell
  py -3 scripts\e2e_uninstall_smoke.py
  ```

What it does:
- Creates temporary dummy project folders with markers (main.py, README.md).
- Validates safety checks and attempts to move to Trash/Recycle Bin when supported.
- Falls back to a non-destructive safe rename if Trash is unavailable.
- Exits 0 on success for all OS cases; non-zero otherwise.

Notes:
- macOS may prompt for Automation permission to allow Finder control.
- Linux requires gio for Trash support; otherwise uses rename fallback.
- Windows uses the Recycle Bin API when run natively on Windows.

## 🖼️ Screenshots

- Splash: assets/screenshots/splash.png
- Setup: assets/screenshots/setup.png
- Showcase: assets/screenshots/showcase.png

## 🧩 Troubleshooting

- Tkinter not available
  - macOS: install Python from python.org or `brew install python`, then recreate `.venv`.
  - Linux: install `python3-tk` (Debian/Ubuntu) or `python3-tkinter` (Fedora/RHEL) and recreate `.venv`.
  - Windows: install Python 3 (includes Tk) and recreate `.venv`.
- 03_hashing_forensics.py is slow
  - Run it from a small directory you intend to scan, not the repo root.
- 02_firewall_parser.py can’t find redhat.txt
  - Place `redhat.txt` in the current working directory or run the script from where the file lives.

---

## 📖 Academic integrity and responsible use

This repository documents my learning. It should not be used to violate the
[UA Code of Academic Integrity](https://deanofstudents.arizona.edu/policies/code-academic-integrity)
or any applicable laws/policies. Keep submissions independent unless collaboration is explicitly allowed and cite sources.

---

## 🤝 Contributing

Pull requests are not accepted directly in this repository (see `.github/workflows/close-prs.yml`).
If you have suggestions, feel free to open an issue or fork the repo and share a link to your changes.

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE).
