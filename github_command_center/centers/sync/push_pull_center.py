from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .base import AsyncGitCenter


class AsyncPushPullCenter(AsyncGitCenter):
    """Extracted guarded pull/push center with background network execution."""

    def __init__(self, parent, repo):
        super().__init__(parent, repo, "Push & Pull Center")
        self.remote = tk.StringVar(value="origin")
        self.branch = tk.StringVar()
        self.pull_mode = tk.StringVar(value="--ff-only")
        self.push_mode = tk.StringVar(value="normal")
        self._build()
        self.refresh()

    def _build(self):
        bar = ttk.Frame(self, padding=8)
        bar.pack(fill="x")
        self.remote_box = ttk.Combobox(bar, textvariable=self.remote, width=16)
        self.remote_box.pack(side="left")
        ttk.Entry(bar, textvariable=self.branch, width=24).pack(side="left", padx=4)
        ttk.Combobox(bar, textvariable=self.pull_mode, values=["--ff-only", "--rebase", "--no-rebase"], state="readonly", width=12).pack(side="left")
        ttk.Button(bar, text="Pull in background", command=self.pull, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Combobox(bar, textvariable=self.push_mode, values=["normal", "set-upstream", "force-with-lease"], state="readonly", width=17).pack(side="left")
        ttk.Button(bar, text="Push in background", command=self.push, style="Accent.TButton").pack(side="left", padx=4)
        self.summary = tk.Text(self, height=12, wrap="word", font=("Consolas", 9), bg="#0f172a", fg="#e2e8f0")
        self.summary.pack(fill="x", padx=8)
        self.add_job_panel()

    def refresh(self):
        remotes = self.git.lines("remote")
        self.remote_box["values"] = remotes
        if remotes and self.remote.get() not in remotes:
            self.remote.set(remotes[0])
        state = self.git.repository_state()
        self.branch.set(state.branch)
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", f"Branch: {state.branch or 'detached'}\nUpstream: {state.upstream or 'none'}\nAhead: {state.ahead}\nBehind: {state.behind}\nWorking tree: {'clean' if state.clean else 'changed'}")

    def pull(self):
        state = self.git.repository_state()
        if not state.clean:
            return messagebox.showwarning("Pull", "Commit or stash local changes before pulling.", parent=self)
        args = ["pull", self.pull_mode.get(), self.remote.get().strip(), self.branch.get().strip()]
        if messagebox.askyesno("Pull", "Run the selected pull strategy in the background?", parent=self):
            self.run_git_async(*args)

    def push(self):
        state = self.git.repository_state()
        if state.detached:
            return messagebox.showwarning("Push", "Create or switch to a branch before pushing.", parent=self)
        args = ["push"]
        mode = self.push_mode.get()
        if mode == "set-upstream":
            args += ["-u"]
        elif mode == "force-with-lease":
            args += ["--force-with-lease"]
            if not messagebox.askyesno("Force with lease", "Push with force-with-lease? Git will reject if the remote changed unexpectedly.", parent=self):
                return
        args += [self.remote.get().strip(), self.branch.get().strip()]
        if mode != "force-with-lease" and not messagebox.askyesno("Push", "Push the selected branch in the background?", parent=self):
            return
        self.run_git_async(*args)
