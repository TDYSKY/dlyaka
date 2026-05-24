"""DLYAKA — minimal cross-platform Tkinter GUI.

Same security model as the CLI: the master password is held only in memory,
never written to disk. Stored key values are never displayed in the UI; only
SHA-256 fingerprints are shown. Copy-to-clipboard auto-clears after 30 s.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
from typing import Optional

from . import __version__
from . import vault as _vault
from .cli import REDACTION_PLACEHOLDER, _fingerprint, _to_env_name
from .vault import SALT_FILE

CLIPBOARD_CLEAR_SECONDS = 30


class DlyakaApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"DLYAKA  v{__version__}  —  Don't Leak Your API Key Again")
        self.geometry("780x520")
        self.minsize(640, 400)
        self._password: Optional[str] = None
        self._clipboard_after_id: Optional[str] = None
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, self._first_unlock)

    # ---------- UI ----------

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        if "aqua" not in style.theme_names():  # use a nicer theme on Linux/Win
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

        toolbar = ttk.Frame(self, padding=(10, 10, 10, 5))
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="Add key", command=self.add_key).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Remove", command=self.remove_key).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Copy value", command=self.copy_to_clipboard).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Run script…", command=self.run_script).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self._refresh_keys).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Lock vault", command=self.lock).pack(side=tk.RIGHT, padx=2)

        list_frame = ttk.LabelFrame(self, text="Stored keys (values are never shown)", padding=8)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("env", "fingerprint")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="tree headings", height=10)
        self.tree.heading("#0", text="Name")
        self.tree.heading("env", text="Env variable")
        self.tree.heading("fingerprint", text="Fingerprint (SHA-256)")
        self.tree.column("#0", width=140, anchor="w")
        self.tree.column("env", width=200, anchor="w")
        self.tree.column("fingerprint", width=400, anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda e: self.copy_to_clipboard())

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        info = ttk.Label(
            self,
            text=(
                "Tip: \"Run script\" injects keys as env vars into the subprocess. "
                "Output is auto-redacted in case a script accidentally prints a key."
            ),
            foreground="#555",
            padding=(10, 0, 10, 0),
        )
        info.pack(fill=tk.X)

        self.status = ttk.Label(self, text="Ready", relief=tk.SUNKEN, anchor=tk.W, padding=4)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------- helpers ----------

    def _set_status(self, msg: str) -> None:
        self.status.configure(text=msg)

    def _first_unlock(self) -> None:
        if not SALT_FILE.exists():
            self._set_status("Welcome — click 'Add key' to create your first vault entry.")
            return
        if self._get_password():
            self._refresh_keys()

    def _get_password(self, confirm: bool = False) -> Optional[str]:
        if self._password is not None and not confirm:
            return self._password
        prompt = "Enter DLYAKA master password:"
        if confirm:
            prompt = "Set a master password for your new vault:"
        pw = simpledialog.askstring("Master password", prompt, show="*", parent=self)
        if not pw:
            return None
        if confirm:
            pw2 = simpledialog.askstring(
                "Confirm password", "Confirm master password:", show="*", parent=self
            )
            if pw != pw2:
                messagebox.showerror("Error", "Passwords do not match.", parent=self)
                return None
        self._password = pw
        return pw

    def _selected_name(self) -> Optional[str]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a key in the list first.", parent=self)
            return None
        return self.tree.item(sel[0], "text")

    # ---------- actions ----------

    def _refresh_keys(self) -> None:
        if self._password is None:
            return
        try:
            keys = _vault.get_all_keys(self._password)
        except ValueError:
            self._password = None
            messagebox.showerror("Error", "Wrong master password — vault locked.", parent=self)
            self._set_status("Locked")
            return

        for row in self.tree.get_children():
            self.tree.delete(row)
        for name, value in sorted(keys.items()):
            self.tree.insert(
                "",
                tk.END,
                text=name,
                values=(_to_env_name(name), _fingerprint(value)),
            )
        self._set_status(f"{len(keys)} key{'s' if len(keys) != 1 else ''} stored")

    def add_key(self) -> None:
        is_new_vault = not SALT_FILE.exists()
        dlg = AddKeyDialog(self)
        self.wait_window(dlg)
        if not dlg.result:
            return
        name, api_key = dlg.result
        pw = self._get_password(confirm=is_new_vault)
        if not pw:
            return
        try:
            _vault.add_key(name, api_key, pw)
        except ValueError as e:
            self._password = None
            messagebox.showerror("Error", str(e), parent=self)
            return
        self._refresh_keys()
        self._set_status(f"Added '{name}' (fingerprint: {_fingerprint(api_key)[:23]}…)")

    def remove_key(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if not messagebox.askyesno(
            "Confirm", f"Delete key '{name}'? This cannot be undone.", parent=self
        ):
            return
        pw = self._get_password()
        if not pw:
            return
        try:
            _vault.remove_key(name, pw)
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", str(e), parent=self)
            return
        self._refresh_keys()
        self._set_status(f"Removed '{name}'")

    def copy_to_clipboard(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if not messagebox.askyesno(
            "Reveal key?",
            f"Copy the value of '{name}' to your clipboard?\n\n"
            f"The clipboard will be cleared automatically after {CLIPBOARD_CLEAR_SECONDS} seconds.",
            parent=self,
        ):
            return
        pw = self._get_password()
        if not pw:
            return
        try:
            value = _vault.get_key(name, pw)
        except (ValueError, KeyError) as e:
            messagebox.showerror("Error", str(e), parent=self)
            return
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update()  # force tkinter to commit the clipboard on Linux
        if self._clipboard_after_id is not None:
            self.after_cancel(self._clipboard_after_id)
        self._clipboard_after_id = self.after(
            CLIPBOARD_CLEAR_SECONDS * 1000, self._clear_clipboard
        )
        self._set_status(
            f"'{name}' copied — clipboard auto-clears in {CLIPBOARD_CLEAR_SECONDS} s"
        )

    def _clear_clipboard(self) -> None:
        self.clipboard_clear()
        self.clipboard_append("")
        self.update()
        self._clipboard_after_id = None
        self._set_status("Clipboard cleared")

    def run_script(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose a script to run with keys injected",
            filetypes=[("Python", "*.py"), ("Shell", "*.sh"), ("All", "*.*")],
            parent=self,
        )
        if not path:
            return
        pw = self._get_password()
        if not pw:
            return
        try:
            keys = _vault.get_all_keys(pw)
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
            return

        env = os.environ.copy()
        for name, value in keys.items():
            env[_to_env_name(name)] = value

        if path.endswith(".py"):
            cmd = [sys.executable, path]
        elif path.endswith(".sh"):
            cmd = ["bash", path]
        else:
            cmd = [path]

        OutputWindow(self, cmd, env, list(keys.values()))
        self._set_status(f"Running {os.path.basename(path)}…")

    def lock(self) -> None:
        self._password = None
        for row in self.tree.get_children():
            self.tree.delete(row)
        self._set_status("Locked — password forgotten")

    def _on_close(self) -> None:
        # Defensive: make sure the clipboard doesn't contain the key when the app exits
        if self._clipboard_after_id is not None:
            self._clear_clipboard()
        self.destroy()


class AddKeyDialog(tk.Toplevel):
    """Modal dialog for adding a key. Value field is masked by default."""

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.title("Add API key")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.result: Optional[tuple] = None

        frm = ttk.Frame(self, padding=15)
        frm.pack()

        ttk.Label(frm, text="Service name").grid(row=0, column=0, sticky="w", pady=(0, 4))
        ttk.Label(
            frm,
            text="(e.g. anthropic, openai, gemini, mistral)",
            foreground="#888",
            font=("", 10),
        ).grid(row=0, column=1, sticky="w", pady=(0, 4))

        self.name_entry = ttk.Entry(frm, width=44)
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(frm, text="API key value").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.key_entry = ttk.Entry(frm, width=44, show="•")
        self.key_entry.grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 4))

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frm,
            text="Show key while typing",
            variable=self.show_var,
            command=self._toggle_show,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 14))

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2)
        ttk.Button(btns, text="Save", command=self._save).pack(side=tk.LEFT, padx=4)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=4)

        self.name_entry.focus_set()
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _toggle_show(self) -> None:
        self.key_entry.configure(show="" if self.show_var.get() else "•")

    def _save(self) -> None:
        name = self.name_entry.get().strip()
        key = self.key_entry.get().strip()
        if not name:
            messagebox.showerror("Missing field", "Enter a service name.", parent=self)
            return
        if not key:
            messagebox.showerror("Missing field", "Enter the API key value.", parent=self)
            return
        self.result = (name, key)
        self.destroy()


class OutputWindow(tk.Toplevel):
    """Live output window for a subprocess. Redacts any stored key value from output."""

    def __init__(self, parent: tk.Tk, cmd: list, env: dict, secrets: list):
        super().__init__(parent)
        self.title(f"Running: {' '.join(cmd)}")
        self.geometry("760x440")
        self.secrets = [s for s in secrets if s and len(s) >= 8]

        self.text = scrolledtext.ScrolledText(
            self,
            bg="#1c1c1c",
            fg="#e0e0e0",
            insertbackground="#fff",
            font=("Courier", 11),
            wrap=tk.NONE,
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.status = ttk.Label(self, text="Running…", anchor=tk.W, padding=4)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        self._stop_event = threading.Event()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        threading.Thread(target=self._run, args=(cmd, env), daemon=True).start()

    def _redact(self, text: str) -> str:
        for s in self.secrets:
            text = text.replace(s, REDACTION_PLACEHOLDER)
        return text

    def _append(self, text: str) -> None:
        self.text.insert(tk.END, text)
        self.text.see(tk.END)

    def _run(self, cmd, env) -> None:
        try:
            proc = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in proc.stdout:  # type: ignore[union-attr]
                if self._stop_event.is_set():
                    proc.terminate()
                    break
                # Marshal to Tk main thread
                self.after(0, self._append, self._redact(line))
            proc.wait()
            self.after(0, self.status.configure, {"text": f"Exited with code {proc.returncode}"})
        except FileNotFoundError as e:
            self.after(0, self._append, f"\n[error] command not found: {e.filename}\n")
            self.after(0, self.status.configure, {"text": "Failed"})
        except Exception as e:  # noqa: BLE001
            self.after(0, self._append, f"\n[error] {e}\n")
            self.after(0, self.status.configure, {"text": "Failed"})

    def _on_close(self) -> None:
        self._stop_event.set()
        self.destroy()


def main() -> None:
    app = DlyakaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
