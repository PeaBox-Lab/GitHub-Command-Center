from __future__ import annotations
import tkinter as tk
from tkinter import messagebox,ttk
from ...services import JobService
from ...ui import JobPanel

class AsyncGitHubWorkflowCenter(tk.Toplevel):
    """Remaining GitHub mutations and workflow operations, all asynchronous."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.jobs=JobService();self.title("GitHub Workflow Center");self.geometry("1120x760");self._build()
    def _build(self):
        f=ttk.Frame(self,padding=8);f.pack(fill="x");self.pr=tk.StringVar();self.workflow=tk.StringVar();self.ref=tk.StringVar(value="main");self.issue_title=tk.StringVar();self.issue_body=tk.StringVar();
        for row,(label,var) in enumerate((("PR number",self.pr),("Workflow",self.workflow),("Ref",self.ref),("Issue title",self.issue_title),("Issue body",self.issue_body))):ttk.Label(f,text=label).grid(row=row,column=0,sticky="w");ttk.Entry(f,textvariable=var).grid(row=row,column=1,sticky="ew",padx=5,pady=2)
        f.columnconfigure(1,weight=1);bar=ttk.Frame(f);bar.grid(row=5,column=0,columnspan=2,sticky="ew",pady=7)
        for text,cmd in (("PR checks",self.pr_checks),("Merge PR",self.merge_pr),("Run workflow",self.run_workflow),("Create issue",self.create_issue),("Rerun failed",self.rerun_failed)):ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=8)
    def start(self,args):
        current=self.jobs.jobs.get(self.panel.active_job_id) if self.panel.active_job_id else None
        if current and current.status in ("Queued","Running"):return messagebox.showwarning("GitHub","Finish or cancel the active request first.",parent=self)
        self.panel.start(args,self.repo)
    def pr_checks(self):
        if self.pr.get().strip():self.start(["gh","pr","checks",self.pr.get().strip(),"--watch"])
    def merge_pr(self):
        n=self.pr.get().strip()
        if n and messagebox.askyesno("Merge PR",f"Squash-merge PR #{n} and delete its branch?",parent=self):self.start(["gh","pr","merge",n,"--squash","--delete-branch"])
    def run_workflow(self):
        if self.workflow.get().strip():self.start(["gh","workflow","run",self.workflow.get().strip(),"--ref",self.ref.get().strip() or "main"])
    def create_issue(self):
        if self.issue_title.get().strip():self.start(["gh","issue","create","--title",self.issue_title.get().strip(),"--body",self.issue_body.get()])
    def rerun_failed(self):self.start(["gh","run","rerun","--failed"])
