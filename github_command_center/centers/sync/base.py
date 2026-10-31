from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ...services import GitService, JobService
from ...ui import JobPanel


class AsyncGitCenter(tk.Toplevel):
    """Common non-blocking base for migrated sync/maintenance centers."""

    def __init__(self, parent, repo: str, title: str):
        super().__init__(parent)
        self.repo = repo
        self.git = GitService(repo)
        self.jobs = JobService()
        self.title(title)
        self.geometry("1100x720")

    def add_job_panel(self):
        self.job_panel = JobPanel(self, self.jobs)
        self.job_panel.pack(fill="both", expand=True, padx=8, pady=8)
        return self.job_panel

    def run_git_async(self, *args: str):
        current_id = getattr(self.job_panel, "active_job_id", None)
        if current_id is not None:
            current = self.jobs.jobs.get(current_id)
            if current and current.status in {"Queued", "Running"}:
                messagebox.showwarning("Operation in progress", "Finish or cancel the active job first.", parent=self)
                return None
        return self.job_panel.start(["git", *args], self.repo)
