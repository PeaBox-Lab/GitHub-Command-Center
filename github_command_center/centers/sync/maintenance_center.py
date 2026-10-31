from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .base import AsyncGitCenter


class AsyncMaintenanceCenter(AsyncGitCenter):
    PRESETS = {
        "Auto maintenance": ("maintenance", "run", "--auto"),
        "Scheduled maintenance": ("maintenance", "run", "--scheduled"),
        "Full object integrity": ("fsck", "--full", "--no-progress"),
        "Normal garbage collection": ("gc",),
        "Write commit graph": ("commit-graph", "write", "--reachable", "--changed-paths"),
        "Verify commit graph": ("commit-graph", "verify", "--shallow"),
        "Write multi-pack index": ("multi-pack-index", "write", "--bitmap"),
    }

    def __init__(self, parent, repo):
        super().__init__(parent, repo, "Repository Maintenance")
        self.action = tk.StringVar(value="Auto maintenance")
        self._build(); self.refresh_status()

    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        ttk.Combobox(bar,textvariable=self.action,values=list(self.PRESETS),state="readonly",width=30).pack(side="left")
        ttk.Button(bar,text="Run in background",command=self.run_selected,style="Accent.TButton").pack(side="left",padx=4)
        ttk.Button(bar,text="Refresh status",command=self.refresh_status).pack(side="left")
        self.status_text=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.status_text.pack(fill="x",padx=8)
        self.add_job_panel()

    def refresh_status(self):
        result=self.git.execute("count-objects","-vH",check=False)
        self.status_text.delete("1.0","end");self.status_text.insert("1.0",result.output)

    def run_selected(self):
        name=self.action.get();args=self.PRESETS[name]
        if name=="Normal garbage collection" and not messagebox.askyesno("Git GC","Run normal garbage collection in the background?",parent=self):return
        self.run_git_async(*args)
