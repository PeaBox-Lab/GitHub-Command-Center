from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .base import AsyncGitCenter


class AsyncFetchCenter(AsyncGitCenter):
    """Migrated fetch center: preview remains synchronous/light, real fetch is async."""

    def __init__(self, parent, repo):
        super().__init__(parent, repo, "Fetch Preview & Execute")
        self.remote = tk.StringVar(value="origin")
        self.refspec = tk.StringVar()
        self.prune = tk.BooleanVar(value=True)
        self.tags = tk.BooleanVar()
        self._build()
        self.refresh_remotes()

    def _build(self):
        bar = ttk.Frame(self, padding=8); bar.pack(fill="x")
        self.remote_box = ttk.Combobox(bar, textvariable=self.remote, width=18)
        self.remote_box.pack(side="left")
        ttk.Entry(bar, textvariable=self.refspec).pack(side="left", fill="x", expand=True, padx=4)
        ttk.Checkbutton(bar, text="Prune", variable=self.prune).pack(side="left")
        ttk.Checkbutton(bar, text="Tags", variable=self.tags).pack(side="left", padx=3)
        ttk.Button(bar, text="Dry run", command=self.preview).pack(side="left")
        ttk.Button(bar, text="Fetch in background", command=self.fetch, style="Accent.TButton").pack(side="left", padx=4)
        self.preview_text = tk.Text(self, height=12, wrap="none", font=("Consolas", 9), bg="#0f172a", fg="#e2e8f0")
        self.preview_text.pack(fill="x", padx=8)
        self.add_job_panel()

    def refresh_remotes(self):
        names = self.git.lines("remote")
        self.remote_box["values"] = names
        if names and self.remote.get() not in names:
            self.remote.set(names[0])
        self.preview()

    def args(self, dry=False):
        args = ["fetch"]
        if dry: args.append("--dry-run")
        if self.prune.get(): args.append("--prune")
        if self.tags.get(): args.append("--tags")
        args.append(self.remote.get().strip())
        if self.refspec.get().strip(): args.append(self.refspec.get().strip())
        return args

    def preview(self):
        result = self.git.execute(*self.args(True), check=False, timeout=120)
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", result.output)

    def fetch(self):
        if messagebox.askyesno("Fetch", f"Run the reviewed fetch from {self.remote.get()} in the background?", parent=self):
            self.run_git_async(*self.args(False))
