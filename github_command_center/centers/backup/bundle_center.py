from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ...services import GitService, JobService
from ...ui import JobPanel


class AsyncBundleCenter(tk.Toplevel):
    """Extracted Git bundle create/verify/list workflow with background create/verify."""

    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.git = GitService(repo)
        self.jobs = JobService()
        self.bundle = tk.StringVar()
        self.title("Git Bundle Center")
        self.geometry("1100x720")
        self._build()

    def _build(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        ttk.Entry(bar, textvariable=self.bundle).pack(side="left", fill="x", expand=True)
        ttk.Button(bar, text="Choose", command=self.choose).pack(side="left", padx=3)
        ttk.Button(bar, text="Create --all", command=self.create, style="Accent.TButton").pack(side="left")
        ttk.Button(bar, text="Verify", command=self.verify).pack(side="left", padx=3)
        ttk.Button(bar, text="List heads", command=self.list_heads).pack(side="left")
        self.output = tk.Text(self, height=12, wrap="none", font=("Consolas", 9), bg="#0f172a", fg="#e2e8f0")
        self.output.pack(fill="x", padx=8)
        self.panel = JobPanel(self, self.jobs)
        self.panel.pack(fill="both", expand=True, padx=8, pady=8)

    def choose(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".bundle", initialfile=f"{Path(self.repo).name}.bundle")
        if path:
            self.bundle.set(path)

    def create(self):
        path = self.bundle.get().strip()
        if not path:
            self.choose(); path = self.bundle.get().strip()
        if path and messagebox.askyesno("Create bundle", "Create a complete --all Git bundle in the background?", parent=self):
            self.panel.start(["git", "bundle", "create", path, "--all"], self.repo)

    def verify(self):
        path = self.bundle.get().strip()
        if path:
            self.panel.start(["git", "bundle", "verify", path], self.repo)

    def list_heads(self):
        path = self.bundle.get().strip()
        if not path:
            return
        result = self.git.execute("bundle", "list-heads", path, check=False)
        self.output.delete("1.0", "end")
        self.output.insert("1.0", result.output)
