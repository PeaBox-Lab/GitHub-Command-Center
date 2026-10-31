from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import GitService,JobService
from ...ui import JobPanel
from ...ui.table_layout import ensure_horizontal_scrollbar

class ReviewCenterV2(tk.Toplevel):
    """Extracted pre-commit/review center with async quality gates."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.jobs=JobService();self.rows=[];self.title("Review Center");self.geometry("1240x800");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Run tests",command=lambda:self.run(["python","-m","unittest","discover","-s","tests","-v"]),style="Accent.TButton").pack(side="left",padx=3);ttk.Button(bar,text="Compile",command=lambda:self.run(["python","-m","compileall","-q","."])).pack(side="left");ttk.Button(bar,text="Ruff",command=lambda:self.run(["ruff","check","github_command_center","tests"])).pack(side="left",padx=3);ttk.Button(bar,text="Bandit",command=lambda:self.run(["bandit","-q","-r","github_command_center","-x","tests"])).pack(side="left")
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=2);pane.add(right,weight=3)
        self.tree=ttk.Treeview(left,columns=("state","path"),show="headings");self.tree.heading("state",text="State");self.tree.heading("path",text="File");self.tree.column("state",width=90);self.tree.column("path",width=500);self.tree.pack(fill="both",expand=True);ensure_horizontal_scrollbar(self.tree,left);self.tree.bind("<<TreeviewSelect>>",lambda e:self.diff())
        self.out=tk.Text(right,height=18,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        raw=self.git.execute("status","--porcelain=v1").stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if len(line)>=4:
                row=(line[:2],line[3:].split(" -> ")[-1]);self.rows.append(row);self.tree.insert("","end",iid=str(len(self.rows)-1),values=row)
        if self.rows:self.tree.selection_set(0);self.diff()
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][1] if s else ""
    def diff(self):
        p=self.selected();r=self.git.execute("diff","--cached" if self.rows and self.rows[int(self.tree.selection()[0])][0][0]!=" " else "--","--",p,check=False) if p else self.git.execute("diff",check=False);self.out.delete("1.0","end");self.out.insert("1.0",r.output)
    def run(self,args):
        current=self.jobs.jobs.get(self.panel.active_job_id) if self.panel.active_job_id else None
        if not current or current.status not in ("Queued","Running"):self.panel.start(args,self.repo)
