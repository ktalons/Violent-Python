#!/usr/bin/env python3
"""
Safe Uninstall — End-to-End Smoke Test

This script validates the "safe uninstall" behavior without touching your repo.
It creates temporary, dummy project folders and exercises the same safety checks
and actions as the app's uninstall helper:
- Strong path checks and project markers
- Prefer moving to OS Trash/Recycle Bin (macOS Finder, Windows API, Linux gio)
- Fallback to a non-destructive safe rename when Trash isn't available

Exit code: 0 on success; non-zero if any OS case fails.

Usage:
  python3 scripts/e2e_uninstall_smoke.py

Notes:
- macOS: May prompt for Automation permissions to control Finder.
- Linux: Requires `gio` for Trash; otherwise will use rename fallback.
- Windows: Uses the Recycle Bin API when running natively on Windows.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def safe_path(p: Path) -> bool:
    try:
        p = p.resolve()
    except Exception:
        return False
    if not p.exists() or not p.is_dir():
        return False
    # Refuse root/home/very-short paths
    if p == Path('/') or p == Path.home() or len(str(p)) < 8:
        return False
    # Require project markers
    if not (p / 'main.py').exists() or not (p / 'README.md').exists():
        return False
    return True


def try_send2trash(path: Path) -> bool:
    try:
        import send2trash  # optional
        send2trash.send2trash(str(path))
        return True
    except Exception:
        return False


def macos_trash(path: Path) -> bool:
    """Use Finder (osascript) to move path to Trash."""
    try:
        escaped = str(path).replace("\\", "\\\\").replace('"', '\\"')
        script = [
            'tell application "Finder"',
            f'delete POSIX file "{escaped}"',
            'end tell',
        ]
        args = ['osascript']
        for line in script:
            args += ['-e', line]
        subprocess.check_call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def linux_trash(path: Path) -> bool:
    """Use gio trash when available (Freedesktop/GLib)."""
    try:
        if shutil.which('gio'):
            subprocess.check_call(['gio', 'trash', str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except Exception:
        pass
    return False


def windows_trash(path: Path) -> bool:
    """Move path to Recycle Bin using SHFileOperation when on Windows."""
    if os.name != 'nt':
        return False
    try:
        import ctypes
        from ctypes import wintypes

        FO_DELETE = 3
        FOF_ALLOWUNDO = 0x0040
        FOF_NOCONFIRMATION = 0x0010

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ('hwnd', wintypes.HWND),
                ('wFunc', wintypes.UINT),
                ('pFrom', wintypes.LPCWSTR),
                ('pTo', wintypes.LPCWSTR),
                ('fFlags', wintypes.UINT),
                ('fAnyOperationsAborted', wintypes.BOOL),
                ('hNameMappings', wintypes.LPVOID),
                ('lpszProgressTitle', wintypes.LPCWSTR),
            ]

        shfo = SHFILEOPSTRUCTW()
        shfo.hwnd = None
        shfo.wFunc = FO_DELETE
        # double-NULL-terminated path list
        shfo.pFrom = str(path) + '\0\0'
        shfo.pTo = None
        shfo.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(shfo))
        return res == 0
    except Exception:
        return False


def safe_rename(path: Path) -> Path | None:
    parent = path.parent
    ts = time.strftime('%Y%m%d_%H%M%S')
    new = parent / f"{path.name}.DELETE_ME_{ts}"
    i = 0
    while new.exists() and i < 50:
        i += 1
        new = parent / f"{path.name}.DELETE_ME_{ts}_{i}"
    try:
        path.rename(new)
        return new
    except Exception:
        return None


def make_dummy_project(prefix: str) -> Path:
    base = Path(tempfile.mkdtemp(prefix=prefix))
    target = base / 'Violent-Python-E2E'
    target.mkdir()
    (target / 'main.py').write_text('print("hello")\n', encoding='utf-8')
    (target / 'README.md').write_text('# E2E\n', encoding='utf-8')
    (target / '.vp_showcase_prefs.json').write_text('{}', encoding='utf-8')
    (target / 'assignments').mkdir()
    return target


def run_case(label: str, mover_funcs: list, simulate_only: bool = False) -> tuple[str, str, bool]:
    t = make_dummy_project(f'vp_e2e_{label.lower()}_')
    assert safe_path(t), f'{label}: safe_path failed unexpectedly for {t}'
    moved = False
    move_used = 'rename'
    if not simulate_only:
        for fn in mover_funcs:
            try:
                if fn(t):
                    moved = True
                    move_used = 'trash'
                    break
            except Exception:
                pass
    if not moved:
        renamed = safe_rename(t)
        ok = renamed is not None and renamed.exists() and not t.exists()
        return (label, 'rename', ok)
    else:
        ok = not t.exists()
        return (label, 'trash', ok)


def main() -> int:
    parser = argparse.ArgumentParser(description='Safe Uninstall E2E Smoke Test')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    results: list[tuple[str, str, bool]] = []

    # macOS
    results.append(run_case('macOS', [try_send2trash, macos_trash], simulate_only=not sys.platform.startswith('darwin')))

    # Linux
    results.append(run_case('Linux', [linux_trash], simulate_only=not (sys.platform.startswith('linux'))))

    # Windows
    # On native Windows, we use Windows API; otherwise simulate to exercise rename fallback
    simulate_windows = not (os.name == 'nt')
    results.append(run_case('Windows', [windows_trash], simulate_only=simulate_windows))

    print('\n[E2E] Summary:')
    all_ok = True
    for os_name, method, ok in results:
        print(f" - {os_name}: {method} -> {'OK' if ok else 'FAIL'}")
        all_ok = all_ok and ok

    if not all_ok:
        print('\nOne or more cases failed.', file=sys.stderr)
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
