import json
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import updater

APP_NAME = "DemoApp"
LOCAL_VERSION = updater.get_local_version()


class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        self.title(f"{APP_NAME}  v{LOCAL_VERSION}")
        self.geometry("600x420")
        self.resizable(False, False)

        self._build_ui()
        self.after(2000, self._start_update_check)

    # ── UI ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = ttk.Frame(self, bootstyle="primary", padding=20)
        header.pack(fill=X)
        ttk.Label(
            header,
            text=APP_NAME,
            font=("Segoe UI", 22, "bold"),
            bootstyle="inverse-primary",
        ).pack(side=LEFT)
        ttk.Label(
            header,
            text=f"v{LOCAL_VERSION}",
            font=("Segoe UI", 11),
            bootstyle="inverse-primary",
        ).pack(side=RIGHT, pady=6)

        # Body
        body = ttk.Frame(self, padding=30)
        body.pack(fill=BOTH, expand=YES)

        ttk.Label(
            body,
            text="Welcome to DemoApp!",
            font=("Segoe UI", 14),
        ).pack(anchor=W, pady=(0, 8))

        ttk.Label(
            body,
            text="This is a minimal ttkbootstrap app demonstrating\n"
                 "automatic update checking and one-click updates.",
            font=("Segoe UI", 10),
            bootstyle="secondary",
        ).pack(anchor=W)

        ttk.Separator(body).pack(fill=X, pady=20)

        ttk.Button(
            body,
            text="Check for updates now",
            bootstyle="outline",
            command=self._start_update_check,
        ).pack(anchor=W)

        # Update banner — hidden until an update is found
        self.update_frame = ttk.Frame(self, bootstyle="warning", padding=(20, 10))
        self.update_version_label = ttk.Label(
            self.update_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            bootstyle="warning",
        )
        self.update_version_label.pack(side=LEFT, expand=YES, anchor=W)

        ttk.Button(
            self.update_frame,
            text="Update now",
            bootstyle="warning",
            command=self._on_update_clicked,
        ).pack(side=RIGHT, padx=(8, 0))

        ttk.Button(
            self.update_frame,
            text="Later",
            bootstyle="outline-warning",
            command=self._hide_update_banner,
        ).pack(side=RIGHT)

        # Progress bar — hidden until download starts
        self.progress_frame = ttk.Frame(self, padding=(20, 10))
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            bootstyle="success-striped",
            length=400,
        )
        self.progress_bar.pack(side=LEFT, padx=(0, 12))
        self.progress_label = ttk.Label(self.progress_frame, text="0%")
        self.progress_label.pack(side=LEFT)

    # ── Update logic ──────────────────────────────────────────────
    def _start_update_check(self):
        updater.check_for_update(
            on_update_available=self._on_update_found,
            on_error=self._on_check_error,
        )

    def _on_update_found(self, latest_version, download_url, notes):
        # Called from background thread — schedule on main thread
        self.after(0, lambda: self._show_update_banner(latest_version, download_url, notes))

    def _on_check_error(self, error_msg):
        # Silently ignore on auto-check; print for debugging
        print(f"[updater] check failed: {error_msg}")

    def _show_update_banner(self, latest_version, download_url, notes):
        self.pending_download_url = download_url
        self.update_version_label.config(
            text=f"Update available: v{latest_version}  —  {notes}"
        )
        self.update_frame.pack(fill=X, side=BOTTOM)

    def _hide_update_banner(self):
        self.update_frame.pack_forget()

    def _on_update_clicked(self):
        self._hide_update_banner()
        self.progress_frame.pack(fill=X, side=BOTTOM, pady=(0, 4))
        self.progress_var.set(0)

        updater.download_and_install(
            url=self.pending_download_url,
            progress_callback=lambda pct: self.after(0, lambda p=pct: self._update_progress(p)),
            done_callback=lambda path: self.after(0, lambda: self._on_download_done(path)),
            error_callback=lambda err: self.after(0, lambda: self._on_download_error(err)),
        )

    def _update_progress(self, pct):
        self.progress_var.set(pct)
        self.progress_label.config(text=f"{pct}%")

    def _on_download_done(self, installer_path):
        self.progress_frame.pack_forget()
        print(f"[updater] installer launched: {installer_path}")
        # App will be replaced by installer — optionally close here:
        # self.destroy()

    def _on_download_error(self, err):
        self.progress_frame.pack_forget()
        ttk.dialogs.Messagebox.show_error(
            title="Update failed",
            message=f"Could not download update:\n{err}",
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()