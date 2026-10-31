from __future__ import annotations
import tkinter as tk
from pathlib import Path
from tkinter import filedialog,ttk
from ..services.readiness_service import ReadinessService

class PublicReleaseReadinessCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Public Release Readiness");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Export JSON",command=self.export).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("check","status","detail"),show="headings")
        for c,t,w in [("check","Check",320),("status","Status",100),("detail","Detail",570)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.summary=tk.StringVar();ttk.Label(self,textvariable=self.summary,padding=8,font=("Segoe UI Semibold",10)).pack(fill="x")
    def refresh(self):
        self.report=ReadinessService(self.repo).assess();self.tree.delete(*self.tree.get_children())
        for c in self.report.checks:self.tree.insert("","end",values=(c.name,c.status,c.detail))
        self.summary.set(f"Score: {self.report.score}% | Required gates: {'PASS' if self.report.passed else 'FAIL'}")
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile="public-release-readiness.json")
        if p:Path(p).write_text(self.report.to_json(),encoding="utf-8")
