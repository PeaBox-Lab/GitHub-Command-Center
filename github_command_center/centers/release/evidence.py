from __future__ import annotations
import datetime,tkinter as tk
from pathlib import Path
from tkinter import filedialog,ttk
from ...services import GitService,JobService
from ...ui import JobPanel

class ReleaseEvidenceV2(tk.Toplevel):
    """Extracted release evidence center; fsck runs asynchronously."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.jobs=JobService();self.title("Release Evidence");self.geometry("1120x760");self._build();self.generate()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Generate summary",command=self.generate).pack(side="left");ttk.Button(bar,text="Run integrity in background",command=self.fsck,style="Accent.TButton").pack(side="left",padx=3);ttk.Button(bar,text="Export Markdown",command=self.export).pack(side="left")
        self.text=tk.Text(self,height=22,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5);self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def safe(self,*args):return self.git.execute(*args,check=False).output
    def generate(self):
        state=self.git.repository_state();tag=self.safe("describe","--tags","--abbrev=0");docs=[]
        for name in ("README.md","CHANGELOG.md","RELEASE_NOTES.md","SECURITY.md","LICENSE"):docs.append((name,(Path(self.repo)/name).exists()))
        self.report=f"# Release Evidence: {Path(self.repo).name}\n\n- Captured: {datetime.datetime.now().isoformat()}\n- Branch: `{state.branch or 'detached'}`\n- HEAD: `{state.head}`\n- Upstream: `{state.upstream or 'none'}`\n- Latest tag: `{tag}`\n- Working tree: **{'CLEAN' if state.clean else 'CHANGED'}**\n\n## Required files\n"+"\n".join(f"- [{'x' if ok else ' '}] {n}" for n,ok in docs)+"\n\n## Recent signatures\n```text\n"+self.safe("log","-10","--pretty=format:%h %G? %s")+"\n```\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def fsck(self):self.panel.start(["git","fsck","--full","--no-progress"],self.repo)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="release-evidence.md")
        if p:Path(p).write_text(self.report,encoding="utf-8")
