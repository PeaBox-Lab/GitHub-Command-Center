from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .base import AsyncGitCenter


class AsyncRemotePruneCenter(AsyncGitCenter):
    def __init__(self, parent, repo):
        super().__init__(parent, repo, "Remote Prune Audit")
        self.remote = tk.StringVar(value="origin")
        self._build(); self.refresh()

    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        self.box=ttk.Combobox(bar,textvariable=self.remote,width=22);self.box.pack(side="left")
        ttk.Button(bar,text="Preview",command=self.preview).pack(side="left",padx=3)
        ttk.Button(bar,text="Prune in background",command=self.prune,style="Accent.TButton").pack(side="left")
        ttk.Button(bar,text="Fetch all + prune",command=lambda:self.run_git_async("fetch","--all","--prune")).pack(side="left",padx=3)
        self.preview_text=tk.Text(self,height=14,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.preview_text.pack(fill="x",padx=8)
        self.add_job_panel()

    def refresh(self):
        names=self.git.lines("remote");self.box["values"]=names
        if names and self.remote.get() not in names:self.remote.set(names[0])
        self.preview()

    def preview(self):
        result=self.git.execute("remote","prune",self.remote.get().strip(),"--dry-run",check=False,timeout=120)
        self.preview_text.delete("1.0","end");self.preview_text.insert("1.0",result.output)

    def prune(self):
        remote=self.remote.get().strip()
        if messagebox.askyesno("Prune remote",f"Prune stale remote-tracking refs for {remote}? Local branches are not deleted.",parent=self):
            self.run_git_async("remote","prune",remote)
