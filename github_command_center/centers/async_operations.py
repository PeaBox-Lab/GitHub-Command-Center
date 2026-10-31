import tkinter as tk
from tkinter import messagebox,ttk
from ..ui import JobPanel
class AsyncOperationsCenter(tk.Toplevel):
    PRESETS={"Fetch all + prune":["git","fetch","--all","--prune"],"Full fsck":["git","fsck","--full","--no-progress"],"Auto maintenance":["git","maintenance","run","--auto"],"Normal gc":["git","gc"],"Write commit graph":["git","commit-graph","write","--reachable","--changed-paths"],"Verify commit graph":["git","commit-graph","verify","--shallow"],"Fetch tags":["git","fetch","--tags"]}
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Async Git Operations");self.geometry("1120x720");self._build()
    def _build(self):
        t=ttk.Frame(self,padding=8);t.pack(fill="x");self.preset=tk.StringVar(value="Fetch all + prune");ttk.Combobox(t,textvariable=self.preset,values=list(self.PRESETS),state="readonly",width=28).pack(side="left");ttk.Button(t,text="Run preset",command=self.run_preset,style="Accent.TButton").pack(side="left",padx=4);ttk.Button(t,text="Repository status",command=lambda:self.run(["git","status","--short","--branch"])).pack(side="left");self.panel=JobPanel(self);self.panel.pack(fill="both",expand=True,padx=8,pady=8)
    def run_preset(self):
        args=self.PRESETS[self.preset.get()]
        if args[-1]=="gc" and not messagebox.askyesno("Git GC","Run normal git gc in the background?",parent=self):return
        self.run(args)
    def run(self,args):
        if self.panel.active_job_id is not None:
            j=self.panel.service.jobs.get(self.panel.active_job_id)
            if j and j.status in ("Queued","Running"):return messagebox.showwarning("Async Git","A job is already active.",parent=self)
        self.panel.start(args,self.repo)
