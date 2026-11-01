from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .base import AsyncGitCenter


class AsyncSubmoduleCenter(AsyncGitCenter):
    def __init__(self, parent, repo):
        super().__init__(parent, repo, "Submodule Center")
        self.url=tk.StringVar();self.path=tk.StringVar();self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        ttk.Entry(bar,textvariable=self.url).pack(side="left",fill="x",expand=True)
        ttk.Entry(bar,textvariable=self.path,width=28).pack(side="left",padx=4)
        for text,cmd in (("Add",self.add),("Sync",lambda:self.run_git_async("submodule","sync","--recursive")),("Update/init",lambda:self.run_git_async("submodule","update","--init","--recursive")),("Status",self.refresh)):
            ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.status_text=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.status_text.pack(fill="x",padx=8)
        self.add_job_panel()
    def refresh(self):
        r=self.git.execute("submodule","status","--recursive",check=False);self.status_text.delete("1.0","end");self.status_text.insert("1.0",r.output)
    def add(self):
        if self.url.get().strip() and self.path.get().strip() and messagebox.askyesno("Submodule",f"Add {self.url.get()} at {self.path.get()}?",parent=self):
            self.run_git_async("submodule","add",self.url.get().strip(),self.path.get().strip())


class AsyncLFSCenter(AsyncGitCenter):
    def __init__(self,parent,repo):
        super().__init__(parent,repo,"Git LFS Center");self.pattern=tk.StringVar(value="*.zip");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Entry(bar,textvariable=self.pattern).pack(side="left",fill="x",expand=True)
        for text,cmd in (("Track pattern",self.track),("Fetch all",lambda:self.run_git_async("lfs","fetch","--all")),("Pull",lambda:self.run_git_async("lfs","pull")),("Prune",self.prune),("Refresh",self.refresh)):
            ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.status_text=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.status_text.pack(fill="x",padx=8);self.add_job_panel()
    def refresh(self):
        r=self.git.execute("lfs","ls-files",check=False);self.status_text.delete("1.0","end");self.status_text.insert("1.0",r.output)
    def track(self):
        p=self.pattern.get().strip()
        if p:self.run_git_async("lfs","track",p)
    def prune(self):
        if messagebox.askyesno("Git LFS","Prune old local LFS objects using Git LFS safety rules?",parent=self):self.run_git_async("lfs","prune")


class AsyncCloneCenter(tk.Toplevel):
    def __init__(self,parent,repo=None):
        super().__init__(parent);from ...services import JobService;from ...ui import JobPanel
        self.jobs=JobService();self.url=tk.StringVar();self.destination=tk.StringVar();self.depth=tk.IntVar(value=0);self.filter=tk.StringVar(value="");self.title("Clone Center");self.geometry("1080x700");self._build(JobPanel)
    def _build(self,JobPanel):
        form=ttk.Frame(self,padding=8);form.pack(fill="x")
        for row,(label,var) in enumerate((("Repository URL",self.url),("Destination",self.destination))):ttk.Label(form,text=label).grid(row=row,column=0,sticky="w");ttk.Entry(form,textvariable=var).grid(row=row,column=1,sticky="ew",padx=5,pady=3)
        ttk.Button(form,text="Browse",command=self.browse).grid(row=1,column=2);ttk.Label(form,text="Depth (0=full)").grid(row=2,column=0,sticky="w");ttk.Spinbox(form,from_=0,to=100000,textvariable=self.depth,width=10).grid(row=2,column=1,sticky="w");ttk.Label(form,text="Partial clone filter").grid(row=3,column=0,sticky="w");ttk.Combobox(form,textvariable=self.filter,values=["","blob:none","tree:0"],width=20).grid(row=3,column=1,sticky="w");form.columnconfigure(1,weight=1);ttk.Button(form,text="Clone in background",command=self.clone,style="Accent.TButton").grid(row=4,column=1,sticky="e",pady=8)
        self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=8)
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.destination.set(p)
    def clone(self):
        if not self.url.get().strip() or not self.destination.get().strip():return
        args=["git","clone"]
        if self.depth.get()>0:args += ["--depth",str(self.depth.get())]
        if self.filter.get().strip():args += ["--filter",self.filter.get().strip()]
        args += [self.url.get().strip(),self.destination.get().strip()]
        if messagebox.askyesno("Clone",f"Clone into {self.destination.get()} in the background?",parent=self):self.panel.start(args,".")
