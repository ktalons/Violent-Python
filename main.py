#!/usr/bin/env python3
import sys
import os
import subprocess
import shlex
import threading
import queue
import re
import keyword
import bisect
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import tempfile
import time
import stat

try:
    from PIL import Image, ImageTk, ImageSequence  # optional for GIF
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


APP_ROOT = Path(__file__).resolve().parent
# Markers used to identify and later close terminals opened by this app
WINDOW_MARKER = "Violent Python Showcase"
CONTENT_MARKER = "[PYTHON SCRIPT RUNNING]"

# Basic logging (only configure if not already configured by caller)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("vp.splash")


def find_logo_path():
    # Prefer GIF (animated) if present; fall back to PNG
    candidates = [
        APP_ROOT / "assets" / "logo.gif",
        APP_ROOT / "assets" / "logo.png",
        APP_ROOT / "assets" / "python-logo.png",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def find_image_logo_path():
    # Only image-based fallbacks
    candidates = [
        APP_ROOT / "assets" / "logo.gif",
        APP_ROOT / "assets" / "logo.png",
        APP_ROOT / "assets" / "python-logo.png",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Violent Python Showcase")
        self._apply_default_geometry()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Simple preferences shared across frames (persisted to disk)
        self.preferences = {
            "macos_terminal_preference": "kitty",
            "linux_terminal_preference": "kitty",
            "windows_terminal_preference": "wt",
        }
        self._load_prefs()

        # Track external terminal processes launched by this app (kitty/wezterm/alacritty/wt/etc.)
        self.open_terms: list[subprocess.Popen] = []

        self.frames = {}
        for F in (SplashFrame, SetupFrame, ShowcaseFrame):
            frame = F(parent=container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("SplashFrame")

    def show_frame(self, name: str):
        frame = self.frames[name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

    def _prefs_path(self) -> Path:
        return APP_ROOT / ".vp_showcase_prefs.json"

    def _load_prefs(self) -> None:
        try:
            p = self._prefs_path()
            if p.exists():
                data = json.load(p.open("r", encoding="utf-8"))
                if isinstance(data, dict):
                    for k in ("macos_terminal_preference", "linux_terminal_preference", "windows_terminal_preference"):
                        if k in data and isinstance(data[k], str):
                            self.preferences[k] = data[k]
                    frn = data.get("first_run_notice")
                    if isinstance(frn, dict):
                        flags = self.preferences.setdefault("first_run_notice", {"macos": False, "windows": False, "linux": False})
                        for key in ("macos", "windows", "linux"):
                            if isinstance(frn.get(key), bool):
                                flags[key] = frn[key]
        except Exception:
            pass

    def save_prefs(self) -> None:
        try:
            p = self._prefs_path()
            json.dump(self.preferences, p.open("w", encoding="utf-8"), indent=2)
        except Exception:
            pass

    def _apply_default_geometry(self) -> None:
        # Default window size set to match provided screenshot
        default_w, default_h = 1052, 768
        min_w, min_h = 1052, 768
        try:
            self.minsize(min_w, min_h)
        except Exception:
            pass
        try:
            self.update_idletasks()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(0, (sw - default_w) // 2)
            # Position a bit higher than exact vertical center for better ergonomics
            y = max(0, (sh - default_h) // 3)
            self.geometry(f"{default_w}x{default_h}+{x}+{y}")
        except Exception:
            # Fallback size if screen metrics are unavailable
            self.geometry(f"{default_w}x{default_h}")

    def on_close(self):
        for frame in self.frames.values():
            if hasattr(frame, "terminate_running_process"):
                frame.terminate_running_process()
        try:
            self.save_prefs()
        except Exception:
            pass
        self.destroy()


class SplashFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        # Footer anchored at bottom center for logo and title
        self.footer = ttk.Frame(self)
        self.footer.pack(side="bottom", pady=30)

        self.logo_label = ttk.Label(self.footer)
        self.logo_label.pack()

        title = ttk.Label(self.footer, text="Violent Python Showcase", font=("Segoe UI", 20, "bold"))
        title.pack(pady=(6, 0))

        subtitle = ttk.Label(self.footer, text="Terminal muscle + GUI ease.", font=("Segoe UI", 12))
        subtitle.pack(pady=(6, 12))

        buttons = ttk.Frame(self.footer)
        buttons.pack(pady=(0, 10))
        ttk.Button(buttons, text="Get Started", command=lambda: controller.show_frame("SetupFrame")).grid(row=0, column=0, padx=8)
        ttk.Button(buttons, text="Skip to Showcase", command=lambda: controller.show_frame("ShowcaseFrame")).grid(row=0, column=1, padx=8)

        self._anim_frames = []
        self._anim_index = 0
        self._anim_job = None
        self._load_logo()

    def _load_logo(self):
        path = find_logo_path()
        if not path:
            logger.warning("Splash: no media found. Add assets/logo.gif or assets/logo.png")
            self.logo_label.config(text="(Add assets/logo.gif or assets/logo.png)")
            return
        logger.info(f"Splash: found media path={path.name} suffix={path.suffix.lower()}")

        # Image/GIF handling (including fallback when video not available)
        if path.suffix.lower() == ".gif":
            if PIL_AVAILABLE:
                try:
                    im = Image.open(path)
                    self._anim_frames = [ImageTk.PhotoImage(frame.convert("RGBA")) for frame in ImageSequence.Iterator(im)]
                    if self._anim_frames:
                        # Ensure label is visible
                        if not self.logo_label.winfo_ismapped():
                            self.logo_label.pack()
                        logger.info(f"Splash: displaying GIF with {len(self._anim_frames)} frames: {path.name}")
                        self._start_animation()
                        return
                except Exception as e:
                    logger.warning(f"Splash: GIF load error {e}; trying tk.PhotoImage")
            try:
                img = tk.PhotoImage(file=str(path))
                if not self.logo_label.winfo_ismapped():
                    self.logo_label.pack()
                self.logo_label.configure(image=img)
                self.logo_label.image = img
                logger.info(f"Splash: displaying GIF via tk.PhotoImage: {path.name}")
                return
            except Exception as e:
                logger.warning(f"Splash: tk.PhotoImage GIF error {e}")

        try:
            if PIL_AVAILABLE:
                im = Image.open(path)
                max_w = 420
                if im.width > max_w:
                    ratio = max_w / im.width
                    im = im.resize((int(im.width * ratio), int(im.height * ratio)))
                photo = ImageTk.PhotoImage(im)
                logger.info(f"Splash: displaying image via PIL: {path.name}")
            else:
                photo = tk.PhotoImage(file=str(path))
                logger.info(f"Splash: displaying image via tk.PhotoImage: {path.name}")
            if not self.logo_label.winfo_ismapped():
                self.logo_label.pack()
            self.logo_label.configure(image=photo)
            self.logo_label.image = photo
        except Exception as e:
            logger.error(f"Splash: image load error {e}; path={path}")
            self.logo_label.config(text=str(path))

    def _start_animation(self):
        if not self._anim_frames:
            return
        self._anim_index = (self._anim_index + 1) % len(self._anim_frames)
        self.logo_label.configure(image=self._anim_frames[self._anim_index])
        self.logo_label.image = self._anim_frames[self._anim_index]
        self._anim_job = self.after(100, self._start_animation)

    def on_show(self):
        if self._anim_frames and self._anim_job is None:
            self._start_animation()

    def terminate_running_process(self):
        # Nothing to stop in Splash when showing static/animated images
        pass


class SetupFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller
        self.proc = None
        self.q = queue.Queue()
        self._pump_job = None

        # Danger style for uninstall (top-right)
        try:
            self._style = getattr(self, "_style", ttk.Style())
            self._style.configure("Danger.TButton", foreground="#b22222", font=("Segoe UI", 10))
        except Exception:
            pass

        # Top bar: title on the left, uninstall in the top-right
        topbar = ttk.Frame(self)
        topbar.pack(fill="x", padx=12, pady=(12, 6))
        header = ttk.Label(topbar, text="Setup", font=("Segoe UI", 16, "bold"))
        header.pack(side="left")
        ttk.Button(topbar, text="⚠ Uninstall", command=self.uninstall_cleanup, style="Danger.TButton", cursor="hand2").pack(side="right")

        desc = ttk.Label(self, text="Install required dependencies from requirements.txt and prepare your environment.")
        desc.pack(anchor="w", padx=12, pady=(0, 12))

        # OS selection row
        os_row = ttk.Frame(self)
        os_row.pack(fill="x", padx=12, pady=(0, 8))
        # Right-side button: Go to Showcase
        right_col = ttk.Frame(os_row)
        right_col.pack(side="right")
        ttk.Button(right_col, text="Go to Showcase", command=lambda: controller.show_frame("ShowcaseFrame")).pack(anchor="e")
        ttk.Label(os_row, text="Choose your OS:").pack(side="left", padx=(0,8))
        self.selected_os = None
        self.btn_linux = ttk.Button(os_row, text="Linux", command=lambda: self.choose_os("linux"))
        self.btn_macos = ttk.Button(os_row, text="MacOS", command=lambda: self.choose_os("macos"))
        self.btn_windows = ttk.Button(os_row, text="Windows", command=lambda: self.choose_os("windows"))
        self.btn_linux.pack(side="left", padx=4)
        self.btn_macos.pack(side="left", padx=4)
        self.btn_windows.pack(side="left", padx=4)

        # Actions for the selected OS
        self.actions = ttk.Frame(self)
        self.actions.pack(fill="x", padx=12, pady=(0, 8))
        # Order: Install | Customize Requirements | Reset preferences (right)
        self.install_os_btn = ttk.Button(self.actions, text="Install", command=self.install_os_packages, state="disabled")
        self.install_os_btn.pack(side="left")
        self.open_req_btn = ttk.Button(self.actions, text="Customize Requirements", command=self.open_selected_requirements_file, state="disabled")
        self.open_req_btn.pack(side="left", padx=8)
        # Reset OS file to defaults (left group)
        self.reset_req_btn = ttk.Button(self.actions, text="Reset Requirements", command=self.reset_requirements_to_defaults, state="disabled")
        self.reset_req_btn.pack(side="left", padx=8)
        # Reset preferences on the right
        self.reset_btn = ttk.Button(self.actions, text="Reset", command=self.reset_preferences)
        self.reset_btn.pack(side="right")

        # Second row for Scan Tool Check, aligned right
        self.tools_actions = ttk.Frame(self)
        self.tools_actions.pack(fill="x", padx=12, pady=(0, 6))
        self.rescan_btn = ttk.Button(self.tools_actions, text="Scan Tool Check", command=self._update_os_tools_ui)
        self.rescan_btn.pack(side="right")

        self.status = ttk.Label(self, text="Select your OS to view and install requirements.")
        self.status.pack(anchor="w", padx=12, pady=(0, 4))
        # Instruction to re-validate tools
        self.scan_note = ttk.Label(
            self,
            text="Tip: Click 'Scan Tool Check' to re-validate terminal requirements before proceeding to the Showcase.",
            foreground="#666",
        )
        self.scan_note.pack(anchor="w", padx=12, pady=(0, 6))
        # OS tools detection summary (colored ✓/✗)
        tools_frame = ttk.Frame(self)
        tools_frame.pack(fill="x", padx=12, pady=(0, 6))
        self.tools_text = tk.Text(tools_frame, height=6, wrap="word")
        self.tools_text.tag_configure("ok", foreground="#22863a")   # green
        self.tools_text.tag_configure("bad", foreground="#d73a49")  # red
        self.tools_text.configure(state="disabled")
        self.tools_text.pack(fill="x", expand=False)

        # macOS preferred terminal selection (shown only when MacOS is selected)
        self.pref_row = ttk.Frame(self)
        ttk.Label(self.pref_row, text="Preferred macOS terminal:").pack(side="left")
        self.macos_pref_var = tk.StringVar(value=getattr(self.controller, "preferences", {}).get("macos_terminal_preference", "kitty"))
        self.macos_pref_combo = ttk.Combobox(self.pref_row, state="readonly", values=["Kitty", "WezTerm", "Alacritty"], width=12)
        # Map internal values to labels and back
        label_map = {"kitty": "Kitty", "wezterm": "WezTerm", "alacritty": "Alacritty"}
        inv_label_map = {v: k for k, v in label_map.items()}
        self.macos_pref_combo.set(label_map.get(self.macos_pref_var.get(), "Kitty"))
        def on_pref_change(_evt=None):
            choice = inv_label_map.get(self.macos_pref_combo.get(), "kitty")
            self.macos_pref_var.set(choice)
            self.controller.preferences["macos_terminal_preference"] = choice
            try:
                self.controller.save_prefs()
            except Exception:
                pass
            try:
                self._write_terminal_pref_to_requirements("macos", choice)
            except Exception:
                pass
            self._update_os_tools_ui()
        self.macos_pref_combo.bind("<<ComboboxSelected>>", on_pref_change)
        self.macos_pref_combo.pack(side="left", padx=8)

        # Linux preferred terminal selection (shown only when Linux is selected)
        self.linux_pref_row = ttk.Frame(self)
        ttk.Label(self.linux_pref_row, text="Preferred Linux terminal:").pack(side="left")
        self.linux_pref_var = tk.StringVar(value=getattr(self.controller, "preferences", {}).get("linux_terminal_preference", "kitty"))
        # Display labels
        linux_values = ["Kitty", "WezTerm", "Alacritty", "GNOME Terminal", "Konsole", "Xterm"]
        self.linux_pref_combo = ttk.Combobox(self.linux_pref_row, state="readonly", values=linux_values, width=16)
        linux_label_map = {
            "kitty": "Kitty",
            "wezterm": "WezTerm",
            "alacritty": "Alacritty",
            "gnome-terminal": "GNOME",
            "konsole": "Konsole",
            "xterm": "Xterm",
        }
        linux_inv_map = {v: k for k, v in linux_label_map.items()}
        self.linux_pref_combo.set(linux_label_map.get(self.linux_pref_var.get(), "Kitty"))
        def on_linux_pref_change(_evt=None):
            choice = linux_inv_map.get(self.linux_pref_combo.get(), "kitty")
            self.linux_pref_var.set(choice)
            self.controller.preferences["linux_terminal_preference"] = choice
            try:
                self.controller.save_prefs()
            except Exception:
                pass
            try:
                self._write_terminal_pref_to_requirements("linux", choice)
            except Exception:
                pass
            self._update_os_tools_ui()
        self.linux_pref_combo.bind("<<ComboboxSelected>>", on_linux_pref_change)
        self.linux_pref_combo.pack(side="left", padx=8)

        # Windows preferred terminal selection (shown only when Windows is selected)
        self.win_pref_row = ttk.Frame(self)
        ttk.Label(self.win_pref_row, text="Preferred Windows terminal:").pack(side="left")
        self.win_pref_var = tk.StringVar(value=getattr(self.controller, "preferences", {}).get("windows_terminal_preference", "wt"))
        win_values = ["Windows Terminal", "Kitty", "WezTerm"]
        self.win_pref_combo = ttk.Combobox(self.win_pref_row, state="readonly", values=win_values, width=18)
        win_label_map = {"wt": "Windows Terminal", "kitty": "Kitty", "wezterm": "WezTerm"}
        win_inv_map = {v: k for k, v in win_label_map.items()}
        self.win_pref_combo.set(win_label_map.get(self.win_pref_var.get(), "Windows Terminal"))
        def on_win_pref_change(_evt=None):
            choice = win_inv_map.get(self.win_pref_combo.get(), "wt")
            self.win_pref_var.set(choice)
            self.controller.preferences["windows_terminal_preference"] = choice
            try:
                self.controller.save_prefs()
            except Exception:
                pass
            try:
                self._write_terminal_pref_to_requirements("windows", choice)
            except Exception:
                pass
            self._update_os_tools_ui()
        self.win_pref_combo.bind("<<ComboboxSelected>>", on_win_pref_change)
        self.win_pref_combo.pack(side="left", padx=8)

        # Help labels for per-OS preferences (packed when OS is selected)
        self.macos_pref_help = ttk.Label(
            self,
            text="Tip: To customize the requirement.txt click button, modify .txt file and save. Then click Install.",
            foreground="#666",
        )
        self.linux_pref_help = ttk.Label(
            self,
            text="Tip: To customize the requirement.txt click button, modify .txt file and save. Then click Install.",
            foreground="#666",
        )
        self.win_pref_help = ttk.Label(
            self,
            text="Tip: To customize the requirement.txt click button, modify .txt file and save. Then click Install.",
            foreground="#666",
        )

        # Regex for parsing vp:terminal metadata in requirements files
        self._vp_terminal_re = re.compile(r"^\s*#\s*vp:terminal\s*=\s*([\w\-]+)\s*$", re.IGNORECASE)

        text_frame = ttk.Frame(self)
        text_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.output = tk.Text(text_frame, height=20, wrap="word")
        yscroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=yscroll.set)
        self.output.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")


    def on_show(self):
        # Auto-select the current OS the first time
        if self.selected_os is None:
            if sys.platform.startswith("darwin"):
                self.choose_os("macos")
            elif os.name == "nt":
                self.choose_os("windows")
            else:
                self.choose_os("linux")

    def _append_log(self, text):
        self.output.insert("end", text)
        self.output.see("end")

    def _pump(self):
        try:
            while True:
                line = self.q.get_nowait()
                self._append_log(line)
        except queue.Empty:
            pass
        if self.proc and self.proc.poll() is None:
            self._pump_job = self.after(50, self._pump)
        else:
            if self.proc:
                code = self.proc.poll()
                self._append_log(f"\n[Process exited with code {code}]\n")
            self.install_os_btn.config(state="normal")
            self.proc = None
            self._pump_job = None

    def get_selected_requirements_file(self) -> Path:
        name = self.selected_os
        if name == "macos":
            return APP_ROOT / "requirements-macos.txt"
        if name == "windows":
            return APP_ROOT / "requirements-windows.txt"
        if name == "linux":
            return APP_ROOT / "requirements-linux.txt"
        return APP_ROOT / "requirements.txt"

    def choose_os(self, name: str):
        self.selected_os = name
        # Sync preference from the selected OS requirements file (vp:terminal=...)
        try:
            self._sync_pref_from_requirements()
        except Exception:
            pass
        # Update button styles (simple visual feedback)
        for btn in (self.btn_linux, self.btn_macos, self.btn_windows):
            btn.state(["!pressed"])  # reset
        if name == "linux":
            self.btn_linux.state(["pressed"])  # visual hint
        elif name == "macos":
            self.btn_macos.state(["pressed"])  # visual hint
        elif name == "windows":
            self.btn_windows.state(["pressed"])  # visual hint
        # Enable actions
        self.install_os_btn.config(state="normal")
        self.open_req_btn.config(state="normal")
        try:
            self.reset_req_btn.config(state="normal")
        except Exception:
            pass
        # Update OS tools detection and Install button availability
        self._update_os_tools_ui()
        # Show preview of requirements file
        self.show_requirements_preview()
        # Show/hide macOS and Linux pref rows, and ensure actions appear after them
        # Temporarily remove actions row to control order
        try:
            self.actions.pack_forget()
        except Exception:
            pass
        if name == "macos":
            try:
                self.pref_row.pack(fill="x", padx=12, pady=(0, 8))
            except Exception:
                pass
            try:
                self.linux_pref_row.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_row.pack_forget()
            except Exception:
                pass
            # Pack help under macOS preference
            try:
                self.linux_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.macos_pref_help.pack(anchor="w", padx=12, pady=(2, 10))
            except Exception:
                pass
        elif name == "linux":
            try:
                self.linux_pref_row.pack(fill="x", padx=12, pady=(0, 8))
            except Exception:
                pass
            try:
                self.pref_row.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_row.pack_forget()
            except Exception:
                pass
            # Pack help under Linux preference
            try:
                self.macos_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.linux_pref_help.pack(anchor="w", padx=12, pady=(2, 10))
            except Exception:
                pass
        elif name == "windows":
            try:
                self.win_pref_row.pack(fill="x", padx=12, pady=(0, 8))
            except Exception:
                pass
            try:
                self.pref_row.pack_forget()
            except Exception:
                pass
            try:
                self.linux_pref_row.pack_forget()
            except Exception:
                pass
            # Pack help under Windows preference
            try:
                self.macos_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.linux_pref_help.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_help.pack(anchor="w", padx=12, pady=(2, 10))
            except Exception:
                pass
        else:
            try:
                self.pref_row.pack_forget()
            except Exception:
                pass
            try:
                self.linux_pref_row.pack_forget()
            except Exception:
                pass
            try:
                self.win_pref_row.pack_forget()
            except Exception:
                pass
            # Hide all help labels
            for lbl in (self.macos_pref_help, self.linux_pref_help, self.win_pref_help):
                try:
                    lbl.pack_forget()
                except Exception:
                    pass
        # Re-pack actions after pref rows so Install appears below the Preferred Terminal row
        try:
            self.actions.pack(fill="x", padx=12, pady=(0, 8))
        except Exception:
            pass

    def show_requirements_preview(self):
        req = self.get_selected_requirements_file()
        # Re-sync preference from file before showing
        try:
            self._sync_pref_from_requirements()
        except Exception:
            pass
        try:
            content = req.read_text(encoding="utf-8") if req.exists() else "(No file found)"
        except Exception as e:
            content = f"[Error reading {req.name}]\n{e}"
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", content)
        self.output.configure(state="disabled")
        self.status.config(text=f"Selected {self.selected_os.upper()} — showing {req.name}")
        # Also refresh tools UI (in case user edited the file or installed tools)
        self._update_os_tools_ui()
        # Ensure open requirements enabled when OS selected
        self.open_req_btn.config(state=("normal" if self.selected_os else "disabled"))

    def install_all(self):
        # If the recommended terminal is missing, open a terminal to install it
        if not self._recommended_tool_present():
            self.install_os_packages()
        # Always install pip requirements for the selected OS
        self.install_pip_for_selected()

    def install_pip_for_selected(self):
        if self.proc:
            return
        req = self.get_selected_requirements_file()
        if not req.exists():
            messagebox.showerror("Install", f"{req.name} not found.")
            return
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req)]
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self._append_log(f"$ {' '.join(cmd)}\n\n")
        # Disable the Install button while pip runs; will be re-enabled in _pump()
        try:
            self.install_os_btn.config(state="disabled")
        except Exception:
            pass

        def reader():
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    cwd=str(APP_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                assert self.proc.stdout is not None
                for line in self.proc.stdout:
                    self.q.put(line)
            except Exception as e:
                self.q.put(f"[Error] {e}\n")

        threading.Thread(target=reader, daemon=True).start()
        self._pump()

    # --- Requirements metadata helpers ---
    def _sync_pref_from_requirements(self):
        req = self.get_selected_requirements_file()
        if not req.exists():
            return
        try:
            text = req.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return
        found = None
        for line in text:
            m = self._vp_terminal_re.match(line)
            if m:
                found = m.group(1).strip().lower()
                break
        if not found:
            return
        # Apply to preferences and UI depending on OS
        if self.selected_os == "macos" and found in ("kitty", "wezterm", "alacritty"):
            self.controller.preferences["macos_terminal_preference"] = found
            try:
                label = {"kitty": "Kitty", "wezterm": "WezTerm", "alacritty": "Alacritty"}[found]
                self.macos_pref_var.set(found)
                self.macos_pref_combo.set(label)
            except Exception:
                pass
        elif self.selected_os == "linux" and found in ("kitty", "konsole", "gnome-terminal", "wezterm", "alacritty"):
            self.controller.preferences["linux_terminal_preference"] = found
            try:
                label = {
                    "kitty": "Kitty",
                    "konsole": "Konsole",
                    "gnome-terminal": "GNOME",
                    "wezterm": "WezTerm",
                    "alacritty": "Alacritty",
                }[found]
                self.linux_pref_var.set(found)
                self.linux_pref_combo.set(label)
            except Exception:
                pass
        elif self.selected_os == "windows" and found in ("wt", "kitty", "wezterm"):
            self.controller.preferences["windows_terminal_preference"] = found
            try:
                label = {"wt": "Windows Terminal", "kitty": "Kitty", "wezterm": "WezTerm"}[found]
                self.win_pref_var.set(found)
                self.win_pref_combo.set(label)
            except Exception:
                pass
        try:
            self.controller.save_prefs()
        except Exception:
            pass

    def _write_terminal_pref_to_requirements(self, os_name: str, value: str):
        # Resolve file based on OS name
        prev = self.selected_os
        self.selected_os = os_name
        req = self.get_selected_requirements_file()
        self.selected_os = prev
        try:
            if not req.exists():
                req.write_text(f"# vp:terminal={value}\n", encoding="utf-8")
                return
            text = req.read_text(encoding="utf-8", errors="ignore").splitlines()
            wrote = False
            for i, line in enumerate(text):
                if self._vp_terminal_re.match(line):
                    text[i] = f"# vp:terminal={value}"
                    wrote = True
                    break
            if not wrote:
                # Prepend metadata line at top to keep it visible
                text = [f"# vp:terminal={value}"] + text
            req.write_text("\n".join(text) + "\n", encoding="utf-8")
        except Exception:
            # Silently ignore write failures to avoid blocking UI
            pass

    def _default_requirements_content(self, os_name: str) -> str:
        if os_name == "macos":
            return (
                "# Violent-Python requirements (macOS)\n"
                "# Edit as needed, then click \"Install\" from the Setup page.\n"
                "# Lines beginning with '#' are comments and ignored by pip.\n"
                "# Non-comment lines are passed directly to pip as package requirements.\n\n"
                "# Terminal preference used by the GUI (editable):\n"
                "# vp:terminal=kitty\n"
                "# Options: kitty, wezterm, alacritty\n\n"
                "# Core assignment dependencies\n"
                "pillow\nprettytable\nrequests\nbeautifulsoup4\n"
                "# Add more packages below as needed for your environment:\n"
                "# rich\n# colorama\n"
            )
        if os_name == "linux":
            return (
                "# Violent-Python requirements (Linux)\n"
                "# Edit as needed, then click \"Install\" from the Setup page.\n"
                "# Lines beginning with '#' are comments and ignored by pip.\n"
                "# Non-comment lines are passed directly to pip as package requirements.\n\n"
                "# Terminal preference used by the GUI (editable):\n"
                "# vp:terminal=kitty\n"
                "# Options: kitty, konsole, gnome-terminal, wezterm, alacritty\n\n"
                "# Core assignment dependencies\n"
                "pillow\nprettytable\nrequests\nbeautifulsoup4\n"
                "# Add more packages below as needed for your environment:\n"
                "# rich\n# colorama\n"
            )
        if os_name == "windows":
            return (
                "# Violent-Python requirements (Windows)\n"
                "# Edit as needed, then click \"Install\" from the Setup page.\n"
                "# Lines beginning with '#' are comments and ignored by pip.\n"
                "# Non-comment lines are passed directly to pip as package requirements.\n\n"
                "# Terminal preference used by the GUI (editable):\n"
                "# vp:terminal=wt\n"
                "# Options: kitty, wt, wezterm\n\n"
                "# Core assignment dependencies\n"
                "pillow\nprettytable\nrequests\nbeautifulsoup4\n"
                "# Add more packages below as needed for your environment:\n"
                "# rich\n# colorama\n"
            )
        return "# Edit as needed\n"

    def reset_requirements_to_defaults(self):
        if not self.selected_os:
            messagebox.showinfo("Reset OS file", "Select an OS first.")
            return
        os_name = self.selected_os
        req = self.get_selected_requirements_file()
        tpl = self._default_requirements_content(os_name)
        try:
            req.write_text(tpl, encoding="utf-8")
            self.status.config(text=f"Reset {req.name} to defaults.")
            self.show_requirements_preview()
        except Exception as e:
            messagebox.showerror("Reset OS file", f"Failed to write {req.name}: {e}")



    def install_os_packages(self):
        # Always run both: OS package setup (terminal + Tk) and pip install for the selected OS file.
        if self.selected_os == "macos":
            # Install the preferred terminal via Homebrew in a new terminal window
            pref = getattr(self.controller, "preferences", {}).get("macos_terminal_preference", "kitty")
            if pref == "kitty":
                install_line = "brew list --cask kitty >/dev/null 2>&1 || brew install --cask kitty; "
                launch_line = "open -a 'kitty'; "
            elif pref == "wezterm":
                install_line = "brew list --cask wezterm >/dev/null 2>&1 || brew install --cask wezterm; "
                launch_line = "open -a 'WezTerm'; "
            elif pref == "alacritty":
                install_line = "brew list --cask alacritty >/dev/null 2>&1 || brew install --cask alacritty; "
                launch_line = "open -a 'Alacritty'; "
            else:
                # Fallback to kitty
                install_line = "brew list --cask kitty >/dev/null 2>&1 || brew install --cask kitty; "
                launch_line = "open -a 'kitty'; "
            cmd = (
                "if command -v brew >/dev/null 2>&1; then "
                f"{install_line}{launch_line}"
                "else echo 'Homebrew not found. Install from https://brew.sh'; fi; "
                "echo; echo 'If prompted by macOS, click Open to allow the terminal to run.'; "
                "echo 'Press Enter to close'; read"
            )
            self._run_os_cmd_in_terminal(cmd)
            # One-time reminder in UI (persisted)
            flags = self.controller.preferences.setdefault("first_run_notice", {"macos": False, "windows": False, "linux": False})
            if not flags.get("macos", False):
                term_label = {"kitty": "Kitty", "wezterm": "WezTerm", "alacritty": "Alacritty"}.get(pref, pref)
                self.status.config(text=f"We launched {term_label} to complete first-run permissions. If terminal didn't open automatically try opening manually before attempting re-installing.")
                flags["macos"] = True
                try:
                    self.controller.save_prefs()
                except Exception:
                    pass
            # Also install pip requirements for the selected OS
            self.install_pip_for_selected()
        elif self.selected_os == "windows":
            # Install the preferred terminal via winget in a new window
            wpref = getattr(self.controller, "preferences", {}).get("windows_terminal_preference", "wt")
            if wpref == "kitty":
                pkg = "Kitty.Kitty"
                post = "if (Get-Command kitty -ErrorAction SilentlyContinue) { Start-Process kitty -ArgumentList '--hold','powershell','-NoExit','-NoLogo','-Command','Write-Host ''Kitty initialized''; Read-Host ''Press Enter to close''' }";
            elif wpref == "wezterm":
                pkg = "WezTerm.WezTerm"
                post = "if (Get-Command wezterm -ErrorAction SilentlyContinue) { Start-Process wezterm -ArgumentList 'start','--','powershell','-NoExit','-NoLogo','-Command','Write-Host ''WezTerm initialized''; Read-Host ''Press Enter to close''' }";
            else:
                pkg = "Microsoft.WindowsTerminal"
                post = "if (Get-Command wt.exe -ErrorAction SilentlyContinue) { Start-Process wt -ArgumentList 'new-window','powershell','-NoExit','-NoLogo','-Command','Write-Host ''Windows Terminal initialized''; Read-Host ''Press Enter to close''' }";
            ps_cmd = (
                f"winget install --id {pkg} -e --accept-source-agreements --accept-package-agreements; "
                + post + "; Write-Host ''; Read-Host 'Press Enter to close'"
            )
            self._run_os_cmd_in_terminal(ps_cmd)
            flags = self.controller.preferences.setdefault("first_run_notice", {"macos": False, "windows": False, "linux": False})
            if not flags.get("windows", False):
                shown = {"wt": "Windows Terminal", "kitty": "Kitty", "wezterm": "WezTerm"}.get(wpref, "Windows Terminal")
                self.status.config(text=f"We launched {shown} to complete first-run initialization. If terminal didn't open automatically try opening manually before attempting re-installing.")
                flags["windows"] = True
                try:
                    self.controller.save_prefs()
                except Exception:
                    pass
            # Also install pip requirements for the selected OS
            self.install_pip_for_selected()
        elif self.selected_os == "linux":
            # Try to install the preferred terminal via the available package manager (sudo may prompt)
            pref = getattr(self.controller, "preferences", {}).get("linux_terminal_preference", "kitty")
            # Map preferred to package name (generally the same) and add Tk package per distro
            pkg = pref
            sh = (
                "if command -v apt-get >/dev/null 2>&1; then "
                f"sudo apt-get update && sudo apt-get install -y {pkg} python3-tk; "
                "elif command -v dnf >/dev/null 2>&1; then "
                f"sudo dnf install -y {pkg} python3-tkinter; "
                "elif command -v pacman >/dev/null 2>&1; then "
                f"sudo pacman -S --noconfirm {pkg} tk; "
                "else echo 'No supported package manager found. Install your preferred terminal and Tk manually.'; fi; "
                # Proactively open the preferred terminal once if available
                f"if command -v {pkg} >/dev/null 2>&1; then "
                f"if [ '{pkg}' = 'kitty' ]; then kitty --hold bash -lc \"echo Initialized; read -p 'Installed: Kitty terminal. Press enter to close installation...'\"; "
                f"elif [ '{pkg}' = 'wezterm' ]; then wezterm start -- bash -lc \"echo Initialized; read -p 'Installed: Wezterm terminal. Press enter to close installation...'\"; "
                f"elif [ '{pkg}' = 'alacritty' ]; then alacritty -e bash -lc \"echo Initialized; read -p 'Installed: Alacritty terminal. Press enter to close installation...'\"; "
                f"elif [ '{pkg}' = 'gnome-terminal' ]; then gnome-terminal --window -- bash -lc \"echo Initialized; read -p 'Installed: GNOME terminal. Press enter to close installation...'\"; "
                f"elif [ '{pkg}' = 'konsole' ]; then konsole --new-window -e bash -lc \"echo Initialized; read -p 'Installed: konsole terminal. Press enter to close installation...'\"; "
                f"elif [ '{pkg}' = 'xterm' ]; then xterm -e bash -lc \"echo Initialized; read -p 'Installed: xterm terminal. Press enter to close installation...'\"; fi; fi; "
                "echo; read -p 'Press Enter to close'"
            )
            self._run_os_cmd_in_terminal(sh)
            flags = self.controller.preferences.setdefault("first_run_notice", {"macos": False, "windows": False, "linux": False})
            if not flags.get("linux", False):
                pretty = {
                    "kitty": "Kitty", "wezterm": "WezTerm", "alacritty": "Alacritty",
                    "gnome-terminal": "GNOME", "konsole": "Konsole", "xterm": "Xterm"
                }.get(pref, pref)
                self.status.config(text=f"We launched {pretty} to complete first-run initialization. If terminal didn't open automatically try opening manually before attempting re-installing.")
                flags["linux"] = True
                try:
                    self.controller.save_prefs()
                except Exception:
                    pass
            # Also install pip requirements for the selected OS
            self.install_pip_for_selected()
        else:
            messagebox.showinfo("Install OS packages", "Select an OS first.")

    # Cross-platform: open a new terminal window and run the given command string
    def _run_os_cmd_in_terminal(self, cmd: str):
        if sys.platform.startswith("darwin"):
            self._macos_run_in_terminal(cmd)
        elif os.name == "nt":
            self._windows_run_in_terminal(cmd)
        else:
            self._linux_run_in_terminal(cmd)

    # macOS helpers
    def _as_escape(self, s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')


    def _has_kitty_macos(self) -> bool:
        return self._check_cmd("kitty") or any(p.exists() for p in [
            Path("/Applications/kitty.app"), Path("/Applications/Kitty.app"),
            Path.home() / "Applications" / "kitty.app", Path.home() / "Applications" / "Kitty.app"
        ])

    def _check_cmd(self, cmd: str) -> bool:
        return shutil.which(cmd) is not None

    def _recommended_tool_present(self) -> bool:
        if self.selected_os == "macos":
            pref = getattr(self.controller, "preferences", {}).get("macos_terminal_preference", "kitty")
            if pref == "kitty":
                return self._has_kitty_macos()
            return self._check_cmd(pref)
        if self.selected_os == "windows":
            wpref = getattr(self.controller, "preferences", {}).get("windows_terminal_preference", "wt")
            if wpref == "kitty":
                return self._check_cmd("kitty")
            if wpref == "wezterm":
                return self._check_cmd("wezterm")
            return self._check_cmd("wt.exe") or self._check_cmd("wt")
        if self.selected_os == "linux":
            pref = getattr(self.controller, "preferences", {}).get("linux_terminal_preference", "kitty")
            return self._check_cmd(pref) or (pref == "gnome-terminal" and self._check_cmd("gnome-terminal"))
        return False

    def _update_os_tools_ui(self):
        if self.selected_os is None:
            self.tools_text.configure(state="normal")
            self.tools_text.delete("1.0", "end")
            self.tools_text.configure(state="disabled")
            self.install_os_btn.config(state="disabled")
            return
        lines = []
        can_skip_install = False
        if self.selected_os == "macos":
            brew = self._check_cmd("brew")
            kitty = self._has_kitty_macos()
            wez = self._check_cmd("wezterm")
            ala = self._check_cmd("alacritty")
            pref = getattr(self.controller, "preferences", {}).get("macos_terminal_preference", "kitty")
            lines.append(f"Homebrew: {'✓' if brew else '✗'}")
            pretty = {"kitty": "Kitty", "wezterm": "WezTerm", "alacritty": "Alacritty"}
            status_map = {"kitty": kitty, "wezterm": wez, "alacritty": ala}
            lines.append(f"Preferred — {pretty.get(pref, pref)}: {'✓' if status_map.get(pref, False) else '✗'}")
            # Also available list
            parts = []
            for name, ok in [("kitty", kitty), ("wezterm", wez), ("alacritty", ala)]:
                if name == pref:
                    continue
                parts.append(f"{pretty.get(name, name)}:{'✓' if ok else '✗'}")
            lines.append("Also available — " + ", ".join(parts))
            can_skip_install = status_map.get(pref, False)
            self.install_os_btn.config(text="Install")
        elif self.selected_os == "windows":
            wt = self._check_cmd("wt.exe") or self._check_cmd("wt")
            winget = self._check_cmd("winget")
            kitty = self._check_cmd("kitty")
            wez = self._check_cmd("wezterm")
            wpref = getattr(self.controller, "preferences", {}).get("windows_terminal_preference", "wt")
            pretty = {"wt": "Windows Terminal", "kitty": "Kitty", "wezterm": "WezTerm"}
            status_map = {"wt": wt, "kitty": kitty, "wezterm": wez}
            lines.append(f"winget: {'✓' if winget else '✗'}")
            lines.append(f"Preferred — {pretty.get(wpref, wpref)}: {'✓' if status_map.get(wpref, False) else '✗'}")
            # Also available
            parts = []
            for key, ok in ("wt", wt), ("kitty", kitty), ("wezterm", wez):
                if key == wpref:
                    continue
                parts.append(f"{pretty.get(key, key)}:{'✓' if ok else '✗'}")
            lines.append("Also available — " + ", ".join(parts))
            can_skip_install = status_map.get(wpref, False)
            self.install_os_btn.config(text="Install")
        else:  # linux
            pref = getattr(self.controller, "preferences", {}).get("linux_terminal_preference", "kitty")
            checks = [
                ("kitty", self._check_cmd("kitty")),
                ("konsole", self._check_cmd("konsole")),
                ("gnome-terminal", self._check_cmd("gnome-terminal")),
                ("wezterm", self._check_cmd("wezterm")),
                ("alacritty", self._check_cmd("alacritty")),
                ("xterm", self._check_cmd("xterm")),
            ]
            status_map = {name: ok for name, ok in checks}
            # Preferred line
            pretty = {
                "kitty": "Kitty",
                "konsole": "Konsole",
                "gnome-terminal": "GNOME",
                "wezterm": "WezTerm",
                "alacritty": "Alacritty",
                "xterm": "Xterm",
            }
            lines.append(f"Preferred — {pretty.get(pref, pref)}: {'✓' if status_map.get(pref, False) else '✗'}")
            # Also available list
            parts = []
            for name, ok in checks:
                if name == pref:
                    continue
                parts.append(f"{name}:{'✓' if ok else '✗'}")
            lines.append("Also available — " + ", ".join(parts))
            can_skip_install = status_map.get(pref, False)
            self.install_os_btn.config(text="Install")
        text = "OS tools check:\n" + "\n".join(lines)
        # Render with colored ✓/✗
        self.tools_text.configure(state="normal")
        self.tools_text.delete("1.0", "end")
        self.tools_text.insert("1.0", text)
        # Apply color tags to all occurrences
        start = "1.0"
        while True:
            idx = self.tools_text.search("✓", start, stopindex="end")
            if not idx:
                break
            end = f"{idx}+1c"
            self.tools_text.tag_add("ok", idx, end)
            start = end
        start = "1.0"
        while True:
            idx = self.tools_text.search("✗", start, stopindex="end")
            if not idx:
                break
            end = f"{idx}+1c"
            self.tools_text.tag_add("bad", idx, end)
            start = end
        self.tools_text.configure(state="disabled")
        self.install_os_btn.config(state=("disabled" if can_skip_install else "normal"))

    def _osascript(self, lines: list[str]):
        args = ["osascript"]
        for line in lines:
            args += ["-e", line]
        subprocess.Popen(args)

    def _macos_run_in_terminal(self, shell_cmd: str):
        # Always use the built-in Terminal to run OS-level setup commands.
        # Prefix with title+marker so we can identify and close these tabs later.
        prefix = f'printf "\\033]0;{WINDOW_MARKER}\\007"; echo "{CONTENT_MARKER}"; '
        cmd = prefix + shell_cmd
        escaped = self._as_escape(cmd)
        self._osascript([
            'tell application "Terminal"',
            'activate',
            f'do script "{escaped}"',
            'end tell',
        ])

    # Windows helper
    def _windows_run_in_terminal(self, ps_cmd: str):
        # Prefix with title + marker so we can identify and close these later
        prefix = f"$Host.UI.RawUI.WindowTitle = '{WINDOW_MARKER}'; Write-Host '{CONTENT_MARKER}'; "
        ps_cmd = prefix + ps_cmd
        wt = shutil.which("wt.exe") or shutil.which("wt")
        if wt:
            p = subprocess.Popen([wt, "new-window", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
        else:
            p = subprocess.Popen(["cmd", "/c", "start", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass

    # Linux helper
    def open_selected_requirements_file(self):
        # Open the OS-selected requirements file in a system editor
        req = self.get_selected_requirements_file()
        if not req.exists():
            try:
                req.touch()
            except Exception as e:
                messagebox.showerror("Open requirements.txt", f"Unable to open {req}: {e}")
                return
        try:
            if self.selected_os == "windows" or os.name == "nt":
                # Prefer Notepad explicitly for clarity
                subprocess.Popen(["notepad", str(req)])
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", str(req)])
            else:
                # Linux: use xdg-open
                subprocess.Popen(["xdg-open", str(req)])
        except Exception as e:
            messagebox.showerror("Open requirements.txt", str(e))

    def reset_preferences(self):
        try:
            # Delete file and restore defaults
            self.controller._prefs_path().unlink(missing_ok=True)
        except Exception:
            pass
        self.controller.preferences = {
            "macos_terminal_preference": "kitty",
            "linux_terminal_preference": "kitty",
            "windows_terminal_preference": "wt",
            "first_run_notice": {"macos": False, "windows": False, "linux": False},
        }
        # Update UI selections
        try:
            self.macos_pref_var.set("kitty")
            self.macos_pref_combo.set("Kitty")
        except Exception:
            pass
        try:
            self.linux_pref_var.set("kitty")
            self.linux_pref_combo.set("Kitty")
        except Exception:
            pass
        try:
            self.win_pref_var.set("wt")
            self.win_pref_combo.set("Windows Terminal")
        except Exception:
            pass
        try:
            self.controller.save_prefs()
        except Exception:
            pass
        self._update_os_tools_ui()
        self.status.config(text="Preferences reset to default settings.")

    def uninstall_cleanup(self):
        # Safer uninstall flow:
        # 1) Inform user that this will move the project to Trash/Recycle Bin when possible
        #    or safely rename the folder, NOT permanently delete it.
        # 2) Require typed confirmation of the folder name.
        folder_name = APP_ROOT.name
        ok = messagebox.askokcancel(
            "Safe Uninstall",
            "WARNING: entire project folder will move to Trash.\n"
            "If Trash fails folder will be renamed (DELETE_ME_).\n\n"
            "System tools are never modified.\n\n"
            "Click OK to continue.",
            icon="warning",
            default="cancel",
        )
        if not ok:
            return
        typed = simpledialog.askstring(
            "Are you Sure?",
            f"Type the project folder name to confirm: {folder_name}",
            parent=self,
        )
        if not typed or typed.strip() != folder_name:
            messagebox.showinfo("Safe Uninstall", "Confirmation did not match. Uninstall canceled.")
            return
        try:
            script_path = self._create_uninstall_script()
        except Exception as e:
            messagebox.showerror("Safe Uninstall", f"Failed to prepare uninstall command: {e}")
            return
        try:
            self._launch_uninstall_script(script_path)
        except Exception as e:
            messagebox.showerror("Safe Uninstall", f"Failed to launch uninstall command: {e}")
            return
        messagebox.showinfo(
            "Safe Uninstall",
            "A terminal window will open to perform the uninstall. This app will now exit so removal can proceed.",
        )
        try:
            self.controller.on_close()
        except Exception:
            # Fallback close
            self.controller.destroy()

    def _create_uninstall_script(self) -> Path:
        # Write a temporary, self-contained Python script that performs a safe uninstall:
        # - Double confirmation
        # - Strong safety checks
        # - Prefer moving to OS Trash/Recycle Bin
        # - Fallback to a non-destructive safe rename (DELETE_ME_...)
        target = APP_ROOT.resolve()
        tmp_dir = Path(tempfile.gettempdir())
        script_path = tmp_dir / f"vp_uninstall_{int(time.time())}.py"
        content_lines = [
            "#!/usr/bin/env python3",
            "import os, sys, shutil, time, stat, subprocess, ctypes",
            "from pathlib import Path",
            "",
            f"TARGET = Path({repr(str(target))})",
            "FOLDER_NAME = TARGET.name",
            "print('Safe Uninstall helper')",
            "print(f'Deleting: {TARGET}')",
            "",
            "# Safety check - refuses dangerous paths",
            "def safe_path(p: Path) -> bool:",
            "    try:",
            "        p = p.resolve()",
            "    except Exception:",
            "        return False",
            "    if not p.exists() or not p.is_dir():",
            "        return False",
            "    # Never operate on root, user home, or extremely short paths",
            "    if p == Path('/') or p == Path.home() or len(str(p)) < 8:",
            "        return False",
            "    # Project markers",
            "    markers = [(p / 'main.py').exists(), (p / 'README.md').exists()]",
            "    if not all(markers):",
            "        return False",
            "    return True",
            "",
            "if not safe_path(TARGET):",
            "    print('[Uninstall] Target path failed safety checks. Aborting.')",
            "    sys.exit(1)",
            "",
            "# Type exact folder name to confirm",
            "try:",
            "    typed = input(f\"Type the project folder name to confirm: {FOLDER_NAME} \")",
            "except EOFError:",
            "    typed = ''",
            "if typed.strip() != FOLDER_NAME:",
            "    print('[Uninstall] Confirmation did not match. Aborting.')",
            "    sys.exit(1)",
            "",
            "def try_send2trash(path: Path) -> bool:",
            "    try:",
            "        import send2trash  # optional, if present",
            "        send2trash.send2trash(str(path))",
            "        return True",
            "    except Exception:",
            "        return False",
            "",
            "def macos_trash(path: Path) -> bool:",
            "    # Use Finder to move to Trash",
            "    try:",
            "        esc = repr(str(path))",
            "        script = [",
            "            'tell application \"Finder\"',",
            "            'delete POSIX file ' + esc,",
            "            'end tell',",
            "        ]",
            "        args = ['osascript']",
            "        for line in script:",
            "            args += ['-e', line]",
            "        subprocess.check_call(args)",
            "        return True",
            "    except Exception:",
            "        return False",
            "",
            "def windows_trash(path: Path) -> bool:",
            "    # Use SHFileOperation with FOF_ALLOWUNDO to send to Recycle Bin",
            "    try:",
            "        from ctypes import wintypes",
            "        FO_DELETE = 3",
            "        FOF_ALLOWUNDO = 0x0040",
            "        FOF_NOCONFIRMATION = 0x0010",
            "        class SHFILEOPSTRUCTW(ctypes.Structure):",
            "            _fields_ = [",
            "                ('hwnd', wintypes.HWND),",
            "                ('wFunc', wintypes.UINT),",
            "                ('pFrom', wintypes.LPCWSTR),",
            "                ('pTo', wintypes.LPCWSTR),",
            "                ('fFlags', wintypes.UINT),",
            "                ('fAnyOperationsAborted', wintypes.BOOL),",
            "                ('hNameMappings', wintypes.LPVOID),",
            "                ('lpszProgressTitle', wintypes.LPCWSTR),",
            "            ]",
            "        shfo = SHFILEOPSTRUCTW()",
            "        shfo.hwnd = None",
            "        shfo.wFunc = FO_DELETE",
            "        # double-NULL-terminated path list",
            "        shfo.pFrom = str(path) + '\\0\\0'",
            "        shfo.pTo = None",
            "        shfo.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION",
            "        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(shfo))",
            "        return res == 0",
            "    except Exception:",
            "        return False",
            "",
            "def linux_trash(path: Path) -> bool:",
            "    # Try gio trash (GNOME/FreeDesktop). Fall back to safe rename if not available.",
            "    try:",
            "        if shutil.which('gio'):",
            "            subprocess.check_call(['gio', 'trash', str(path)])",
            "            return True",
            "    except Exception:",
            "        pass",
            "    return False",
            "",
            "def safe_rename(path: Path) -> Path | None:",
            "    parent = path.parent",
            "    ts = time.strftime('%Y%m%d_%H%M%S')",
            "    new = parent / (path.name + '.DELETE_ME_' + ts)",
            "    # Avoid collisions",
            "    i = 0",
            "    while new.exists() and i < 50:",
            "        i += 1",
            "        new = parent / (path.name + '.DELETE_ME_' + ts + '_' + str(i))",
            "    try:",
            "        path.rename(new)",
            "        return new",
            "    except Exception:",
            "        return None",
            "",
            "# Allow GUI to close any file handles",
            "time.sleep(1.0)",
            "",
            "moved = False",
            "# First, try optional send2trash if installed",
            "if try_send2trash(TARGET):",
            "    print('[Uninstall] Sending to Trash.')",
            "    moved = True",
            "else:",
            "    if sys.platform.startswith('darwin'):",
            "        if macos_trash(TARGET):",
            "            print('[Uninstall] Moved to Trash.')",
            "            moved = True",
            "    elif os.name == 'nt':",
            "        if windows_trash(TARGET):",
            "            print('[Uninstall] Moved to Recycle Bin.')",
            "            moved = True",
            "    else:",
            "        if linux_trash(TARGET):",
            "            print('[Uninstall] Moved to Trash.')",
            "            moved = True",
            "",
            "if not moved:",
            "    print('[Uninstall] Trash not available. Performing non-destructive safe rename...')",
            "    renamed = safe_rename(TARGET)",
            "    if renamed is None:",
            "        print('[Uninstall] Safe rename failed. No changes were made. Aborting.')",
            "        sys.exit(1)",
            "    print(f'[Uninstall] Folder renamed to: {renamed}')",
            "",
            "print('[Uninstall] Complete. You can restore from Trash or delete the renamed folder manually.')",
        ]
        content = "\n".join(content_lines) + "\n"
        script_path.write_text(content, encoding="utf-8")
        os.chmod(script_path, 0o700)
        return script_path

    def _launch_uninstall_script(self, script_path: Path):
        # Run the uninstall script in a new terminal window depending on OS
        if sys.platform.startswith("darwin"):
            cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(script_path))}; echo; echo 'Successful. Press Enter to shutdown'; read"
            self._macos_run_in_terminal(cmd)
        elif os.name == "nt":
            py = sys.executable.replace('/', '\\')
            sp = str(script_path).replace('/', '\\')
            ps_cmd = f"& '{py}' '{sp}'; Write-Host ''; Read-Host 'Successful. Press Enter to shutdown'"
            self._windows_run_in_terminal(ps_cmd)
        else:
            cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(script_path))}; echo; read -p 'Successful. Press Enter to shutdown'"
            self._linux_run_in_terminal(cmd)

    def _linux_run_in_terminal(self, sh_cmd: str):
        # Wrap in bash -lc when launching emulators; prefix with title+marker
        prefix = f'printf "\\033]0;{WINDOW_MARKER}\\007"; echo "{CONTENT_MARKER}"; '
        sh_cmd = prefix + sh_cmd
        candidates = []
        if shutil.which("kitty"):
            candidates.append(["kitty", "--hold", "bash", "-lc", sh_cmd])
        if shutil.which("alacritty"):
            candidates.append(["alacritty", "-e", "bash", "-lc", sh_cmd])
        if shutil.which("wezterm"):
            candidates.append(["wezterm", "start", "--", "bash", "-lc", sh_cmd])
        if shutil.which("gnome-terminal"):
            candidates.append(["gnome-terminal", "--window", "--", "bash", "-lc", sh_cmd])
        if shutil.which("konsole"):
            candidates.append(["konsole", "--new-window", "-e", "bash", "-lc", sh_cmd])
        if shutil.which("xterm"):
            candidates.append(["xterm", "-e", "bash", "-lc", sh_cmd])
        if shutil.which("x-terminal-emulator"):
            candidates.append(["x-terminal-emulator", "-e", "bash", "-lc", sh_cmd])
        for tcmd in candidates:
            try:
                p = subprocess.Popen(tcmd)
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
            except FileNotFoundError:
                continue
        messagebox.showerror("No supported terminal emulator found. Install supported OS packages on Setup screen.")

    def terminate_running_process(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass


class ShowcaseFrame(ttk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        self.controller = controller

        header = ttk.Label(self, text="Showcase", font=("Segoe UI", 16, "bold"))
        header.pack(anchor="w", padx=12, pady=(12, 6))

        topbar = ttk.Frame(self)
        topbar.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Button(topbar, text="Refresh", command=self.refresh_scripts).pack(side="left")
        self.run_term_btn = ttk.Button(topbar, text="Run in Terminal ▶", command=self.run_in_terminal, state="disabled")
        self.run_term_btn.pack(side="left", padx=8)
        ttk.Button(topbar, text="Back to Setup", command=lambda: controller.show_frame("SetupFrame")).pack(side="right")

        main = ttk.Panedwindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=12, pady=8)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=3)

        ttk.Label(left, text="Assignments:").pack(anchor="w")
        self.listbox = tk.Listbox(left, height=20, exportselection=False)
        self.listbox.pack(fill="both", expand=True, pady=(4, 8))
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select)
        # Keep an ordered list of script paths aligned with the listbox items
        self.scripts = []

        # Code preview area
        self.path_label = ttk.Label(right, text="Code preview: select an option to preview", foreground="#666")
        self.path_label.pack(anchor="w")
        code_frame = ttk.Frame(right)
        code_frame.pack(fill="both", expand=True)
        self.code_text = tk.Text(code_frame, wrap="none", font=("Menlo", 12))
        xscroll = ttk.Scrollbar(code_frame, orient="horizontal", command=self.code_text.xview)
        yscroll = ttk.Scrollbar(code_frame, orient="vertical", command=self.code_text.yview)
        self.code_text.configure(xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.code_text.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(side="bottom", fill="x")
        self._setup_code_tags()
        self.code_text.config(state="disabled")

        hint = ttk.Label(right, text="Tip: Use 'Run in Terminal' for full interactivity.", foreground="#666")
        hint.pack(anchor="w", pady=(4, 6))

        # Footer with Close button at the bottom-right
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x", padx=12, pady=(0, 12))
        ttk.Button(footer, text="Close", command=self.close_all).pack(side="right")

        self.refresh_scripts()

    def on_show(self):
        self.refresh_scripts()
        self._load_preview()

    def on_list_select(self, _event=None):
        self._update_buttons()
        self._load_preview()

    def _update_buttons(self):
        sel = self._selected_script_path() is not None
        self.run_term_btn.config(state="normal" if sel else "disabled")

    def refresh_scripts(self):
        self.listbox.delete(0, "end")
        scripts = []
        assign_dir = APP_ROOT / "assignments"
        if assign_dir.exists():
            # Discover Python files inside immediate subdirectories (nested layout)
            scripts = list(assign_dir.glob("*/*.py"))
        # Sort by numeric prefix:
        # - Prefer numeric prefix from the first subdirectory (e.g., 00_showcase_check/),
        # - Fallback to numeric prefix on the filename stem,
        # - Then alphabetical.
        def sort_key(p: Path):
            try:
                rel = p.relative_to(assign_dir)
                first = rel.parts[0] if len(rel.parts) >= 2 else ""
            except Exception:
                first = ""
            m_dir = re.match(r"^(\d+)", first)
            m_file = re.match(r"^(\d+)", p.stem)
            primary = int(m_dir.group(1)) if m_dir else (int(m_file.group(1)) if m_file else 10**9)
            return (primary, first.lower(), p.stem.lower())
        scripts.sort(key=sort_key)
        # Save paths aligned with listbox entries
        self.scripts = scripts
        for p in scripts:
            # Display friendly title derived from filename
            self.listbox.insert("end", self._friendly_label(p))
        self._update_buttons()

    def _selected_script_path(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        idx = sel[0]
        if 0 <= idx < len(getattr(self, "scripts", [])):
            return self.scripts[idx]
        return None

    def _friendly_label(self, p: Path) -> str:
        name = p.stem
        m = re.match(r"^(\d+)[-_](.+)$", name, re.IGNORECASE)
        base = m.group(2) if m else name
        base = re.sub(r"[_\-]+", " ", base).strip()
        base = base if base else name
        # Title-case then restore acronyms
        title = base.title()
        acronyms = {
            "api": "API",
            "pil": "PIL",
            "tcp": "TCP",
            "udp": "UDP",
            "pcap": "PCAP",
            "http": "HTTP",
            "https": "HTTPS",
            "url": "URL",
            "ip": "IP",
            "dns": "DNS",
            "ssl": "SSL",
            "tls": "TLS",
            "id3": "ID3",
            "nltk": "NLTK",
            "ml": "ML",
            "oop": "OOP",
            "exif": "EXIF",
            "lsb": "LSB",
            "mp3": "MP3",
            "sha1": "SHA1",
            "md5": "MD5",
            "sha256": "SHA256",
            "csv": "CSV",
            "json": "JSON",
        }
        words = title.split()
        words = [acronyms.get(w.lower(), w) for w in words]
        return " ".join(words)

    def _setup_code_tags(self):
        t = self.code_text
        # Basic, readable color scheme compatible with light/dark themes
        t.tag_configure("py_keyword", foreground="#005cc5", font=("Menlo", 12, "bold"))
        t.tag_configure("py_string", foreground="#22863a")
        t.tag_configure("py_comment", foreground="#6a737d", font=("Menlo", 12, "italic"))
        t.tag_configure("py_number", foreground="#6f42c1")
        t.tag_configure("py_decorator", foreground="#e36209")
        t.tag_configure("py_defname", foreground="#d73a49")
        t.tag_configure("py_classname", foreground="#d73a49")

        # Keep a list handy for clearing
        self._py_tags = [
            "py_keyword",
            "py_string",
            "py_comment",
            "py_number",
            "py_decorator",
            "py_defname",
            "py_classname",
        ]

    def _clear_highlight_tags(self):
        for tag in getattr(self, "_py_tags", []):
            self.code_text.tag_remove(tag, "1.0", "end")

    def _highlight_code(self, content: str):
        # Precompute line starts so we can convert offsets to Tk indices efficiently
        line_starts = [0]
        for m in re.finditer("\n", content):
            line_starts.append(m.end())

        def to_index(pos: int) -> str:
            line_idx = bisect.bisect_right(line_starts, pos) - 1
            col = pos - line_starts[line_idx]
            return f"{line_idx + 1}.{col}"

        def apply(pattern: re.Pattern, tag: str, group: int | None = None):
            for m in pattern.finditer(content):
                start = m.start(group or 0)
                end = m.end(group or 0)
                self.code_text.tag_add(tag, to_index(start), to_index(end))

        # Patterns
        triple = re.compile(r"('''.*?'''|\"\"\".*?\"\"\")", re.DOTALL)
        string_ = re.compile(r"('([^'\\\n]|\\.)*'|\"([^\"\\\n]|\\.)*\")")
        comment = re.compile(r"#.*", re.MULTILINE)
        decorator = re.compile(r"(?m)^\s*@\w+")
        # Keywords
        kw = re.compile(r"\\b(" + "|".join(re.escape(k) for k in keyword.kwlist) + r")\\b")
        # Numbers (simple)
        number = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
        # def/class names
        defname = re.compile(r"\bdef\s+(\w+)")
        classname = re.compile(r"\bclass\s+(\w+)")

        # Order: strings first, then comments, then decorators/keywords/numbers/names
        apply(triple, "py_string")
        apply(string_, "py_string")
        apply(comment, "py_comment")
        apply(decorator, "py_decorator")
        apply(kw, "py_keyword")
        apply(number, "py_number")
        apply(defname, "py_defname", group=1)
        apply(classname, "py_classname", group=1)

    def _load_preview(self):
        path = self._selected_script_path()
        self.code_text.config(state="normal")
        self.code_text.delete("1.0", "end")
        self._clear_highlight_tags()
        if not path or not path.exists():
            self.path_label.config(text="Code preview: select an option to preview")
            self.code_text.config(state="disabled")
            return
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            content = f"[Error reading file]\n{e}"
        self.path_label.config(text=f"Code preview: {path.relative_to(APP_ROOT)}")
        self.code_text.insert("1.0", content)
        self._highlight_code(content)
        self.code_text.config(state="disabled")

    def run_in_terminal(self):
        path = self._selected_script_path()
        if not path or not path.exists():
            messagebox.showerror("Run in Terminal", "Select a python script to run.")
            return
        try:
            if sys.platform == "darwin":
                self._run_in_macos_terminal(path)
            elif os.name == "nt":
                self._run_in_windows_terminal(path)
            else:
                self._run_in_linux_terminal(path)
        except Exception as e:
            messagebox.showerror("Run in Terminal", str(e))

    def _as_escape(self, s: str) -> str:
        # Escape for inclusion inside a double-quoted AppleScript string
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def _has_kitty_macos(self) -> bool:
        return shutil.which("kitty") is not None or any(p.exists() for p in [
            Path("/Applications/kitty.app"), Path("/Applications/Kitty.app"),
            Path.home() / "Applications" / "kitty.app", Path.home() / "Applications" / "Kitty.app"
        ])

    def _osascript(self, lines: list[str]):
        args = ["osascript"]
        for line in lines:
            args += ["-e", line]
        subprocess.Popen(args)

    def _run_in_macos_terminal(self, script_path: Path):
        repo = APP_ROOT
        rel = script_path.relative_to(APP_ROOT)
        # Use a login shell so user env applies; activate venv if present, then run
        cmd = (
            f"printf \"\\033]0;{WINDOW_MARKER}\\007\"; echo \"{CONTENT_MARKER}\"; "
            f"cd {shlex.quote(str(repo))}; "
            f"if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi; "
            f"{shlex.quote(sys.executable)} {shlex.quote(str(rel))}; "
            f"echo; echo 'Successful. Press Enter to shutdown'; read"
        )
        # Prefer macOS terminals similar to Linux: kitty -> wezterm -> alacritty
        pref = getattr(self.controller, "preferences", {}).get("macos_terminal_preference", "kitty")
        order = [pref] + [t for t in ["kitty", "wezterm", "alacritty"] if t != pref]
        for term in order:
            if not shutil.which(term):
                continue
            if term == "kitty":
                p = subprocess.Popen(["kitty", "--title", WINDOW_MARKER, "--hold", "bash", "-lc", cmd])
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
            if term == "wezterm":
                p = subprocess.Popen(["wezterm", "start", "--", "bash", "-lc", cmd])
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
            if term == "alacritty":
                p = subprocess.Popen(["alacritty", "--title", WINDOW_MARKER, "-e", "bash", "-lc", cmd])
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
        messagebox.showerror("Run in Terminal", "No supported macOS terminal found. Install one from Setup first.")

    def _run_in_windows_terminal(self, script_path: Path):
        repo = str(APP_ROOT)
        rel = str(script_path.relative_to(APP_ROOT)).replace("/", "\\")
        py = sys.executable.replace("/", "\\")
        ps_cmd = (
            f"$Host.UI.RawUI.WindowTitle = '{WINDOW_MARKER}'; Write-Host '{CONTENT_MARKER}'; "
            f"Set-Location -Path '{repo}'; "
            f"if (Test-Path .venv\\Scripts\\Activate.ps1) {{ . .venv\\Scripts\\Activate.ps1 }}; "
            f"& '{py}' '{rel}'; "
            f"Write-Host ''; Read-Host 'Successful. Press Enter to shutdown'"
        )
        wpref = getattr(self.controller, "preferences", {}).get("windows_terminal_preference", "wt")
        # Try preferred first
        if wpref == "kitty" and shutil.which("kitty"):
            p = subprocess.Popen(["kitty", "--title", WINDOW_MARKER, "--hold", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
            return
        if wpref == "wezterm" and shutil.which("wezterm"):
            p = subprocess.Popen(["wezterm", "start", "--", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
            return
        if wpref == "wt":
            wt = shutil.which("wt.exe") or shutil.which("wt")
            if wt:
                p = subprocess.Popen([wt, "new-window", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
        # Fallback order: wt -> wezterm -> kitty -> powershell
        wt = shutil.which("wt.exe") or shutil.which("wt")
        if wt:
            p = subprocess.Popen([wt, "new-window", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
            return
        if shutil.which("wezterm"):
            p = subprocess.Popen(["wezterm", "start", "--", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
            return
        if shutil.which("kitty"):
            p = subprocess.Popen(["kitty", "--title", WINDOW_MARKER, "--hold", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
            try:
                self.controller.open_terms.append(p)
            except Exception:
                pass
            return
        # Final fallback: plain PowerShell window
        p = subprocess.Popen(["cmd", "/c", "start", "powershell", "-ExecutionPolicy", "Bypass", "-NoExit", "-NoLogo", "-Command", ps_cmd])
        try:
            self.controller.open_terms.append(p)
        except Exception:
            pass

    def _run_in_linux_terminal(self, script_path: Path):
        repo = APP_ROOT
        rel = script_path.relative_to(APP_ROOT)
        cmd = (
            f"printf \"\\033]0;{WINDOW_MARKER}\\007\"; echo \"{CONTENT_MARKER}\"; "
            f"cd {shlex.quote(str(repo))}; "
            f"if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi; "
            f"{shlex.quote(sys.executable)} {shlex.quote(str(rel))}; "
            f"echo; echo 'Successful. Press Enter to shutdown'; read"
        )
        # Prefer user-selected terminal; fallback to others in order
        base = ["kitty", "wezterm", "alacritty", "gnome-terminal", "konsole", "xterm", "x-terminal-emulator"]
        pref = getattr(self.controller, "preferences", {}).get("linux_terminal_preference", "kitty")
        order = [pref] + [t for t in base if t != pref]
        for term in order:
            if not shutil.which(term):
                continue
            if term == "kitty":
                tcmd = ["kitty", "--title", WINDOW_MARKER, "--hold", "bash", "-lc", cmd]
            elif term == "alacritty":
                tcmd = ["alacritty", "--title", WINDOW_MARKER, "-e", "bash", "-lc", cmd]
            elif term == "wezterm":
                tcmd = ["wezterm", "start", "--", "bash", "-lc", cmd]
            elif term == "gnome-terminal":
                tcmd = ["gnome-terminal", "--window", "--", "bash", "-lc", cmd]
            elif term == "konsole":
                tcmd = ["konsole", "--new-window", "-e", "bash", "-lc", cmd]
            elif term == "xterm":
                tcmd = ["xterm", "-e", "bash", "-lc", cmd]
            else:  # x-terminal-emulator
                tcmd = ["x-terminal-emulator", "-e", "bash", "-lc", cmd]
            try:
                p = subprocess.Popen(tcmd)
                try:
                    self.controller.open_terms.append(p)
                except Exception:
                    pass
                return
            except FileNotFoundError:
                continue
        raise RuntimeError("No supported terminal emulator found. Install supported terminal listed on Setup screen")

    def terminate_running_process(self):
        # No in-app subprocess is kept running in this mode
        pass

    def close_all(self):
        # Attempt to close external terminal windows opened by this app,
        # then close the GUI.
        try:
            # Close terminals we spawned directly (kitty/wezterm/alacritty/wt/etc.)
            terms = list(getattr(self.controller, "open_terms", []))
            for p in terms:
                try:
                    if p and p.poll() is None:
                        p.terminate()
                except Exception:
                    pass
            # brief grace period
            time.sleep(0.2)
            for p in terms:
                try:
                    if p and p.poll() is None:
                        p.kill()
                except Exception:
                    pass
            try:
                self.controller.open_terms = []
            except Exception:
                pass
        except Exception:
            pass

        # macOS Terminal: close tabs/windows that contain our marker
        if sys.platform.startswith("darwin"):
            try:
                lines = [
                    'tell application "Terminal"',
                    'try',
                    'repeat with w in windows',
                    'repeat with t in tabs of w',
                    'try',
                    'set c to contents of t',
                    'on error',
                    'set c to ""',
                    'end try',
                    f'if c contains "{CONTENT_MARKER}" then',
                    'try',
                    'close t',
                    'end try',
                    'end if',
                    'end repeat',
                    'end repeat',
                    'end try',
                    'end tell',
                ]
                args = ["osascript"]
                for l in lines:
                    args += ["-e", l]
                subprocess.Popen(args)
            except Exception:
                pass

        # Finally, close the GUI
        try:
            self.controller.on_close()
        except Exception:
            try:
                self.controller.destroy()
            except Exception:
                pass


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
