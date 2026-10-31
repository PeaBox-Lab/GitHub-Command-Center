from __future__ import annotations
import tkinter as tk
from tkinter import messagebox,ttk
from ...services import JobService
from ...ui import JobPanel

class AsyncGitHubCenter(tk.Toplevel):
    """Unified asynchronous gh CLI API center for GitHub network calls."""
    PRESETS={
        "Repository details":["gh","repo","view","--json","nameWithOwner,description,visibility,defaultBranchRef,issues,pullRequests"],
        "Pull requests":["gh","pr","list","--limit","100","--json","number,title,state,isDraft,author,updatedAt"],
        "Issues":["gh","issue","list","--limit","100","--json","number,title,state,author,updatedAt"],
        "Workflow runs":["gh","run","list","--limit","50","--json","databaseId,workflowName,status,conclusion,headBranch,updatedAt"],
        "Releases":["gh","release","list","--limit","50"],
        "Dependabot alerts":["gh","api","repos/{owner}/{repo}/dependabot/alerts"],
        "Code scanning alerts":["gh","api","repos/{owner}/{repo}/code-scanning/alerts"],
        "Secret scanning alerts":["gh","api","repos/{owner}/{repo}/secret-scanning/alerts"],
    }
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.jobs=JobService();self.title("GitHub Network Center");self.geometry("1120x740");self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.action=tk.StringVar(value="Repository details");ttk.Combobox(bar,textvariable=self.action,values=list(self.PRESETS),state="readonly",width=30).pack(side="left");ttk.Button(bar,text="Run in background",command=self.run,style="Accent.TButton").pack(side="left",padx=4);ttk.Button(bar,text="Check authentication",command=lambda:self.start(["gh","auth","status"])).pack(side="left")
        self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=8);ttk.Label(self,text="All GitHub API/CLI network calls run through JobService with streamed output and cancellation. Authentication remains managed by `gh auth login`.",padding=8).pack(fill="x")
    def start(self,args):
        current=self.jobs.jobs.get(self.panel.active_job_id) if self.panel.active_job_id else None
        if current and current.status in ("Queued","Running"):return messagebox.showwarning("GitHub","Finish or cancel the active request first.",parent=self)
        self.panel.start(args,self.repo)
    def run(self):self.start(self.PRESETS[self.action.get()])
