from __future__ import annotations
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
from ...services import GitService,JobService
from ...ui import JobPanel

class ReleasePublishCenterV2(tk.Toplevel):
    """Extracted guarded tag/GitHub Release publishing center."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.jobs=JobService();self.title("Release Publish Center");self.geometry("1120x760");self._build();self.refresh()
    def _build(self):
        form=ttk.Frame(self,padding=8);form.pack(fill="x");self.tag=tk.StringVar();self.title_var=tk.StringVar();self.notes=tk.StringVar();self.draft=tk.BooleanVar(value=True);self.prerelease=tk.BooleanVar();self.asset=tk.StringVar()
        for row,(label,var) in enumerate((("Tag",self.tag),("Title",self.title_var),("Notes file",self.notes),("Asset",self.asset))):ttk.Label(form,text=label).grid(row=row,column=0,sticky="w",pady=3);ttk.Entry(form,textvariable=var).grid(row=row,column=1,sticky="ew",padx=6,pady=3)
        form.columnconfigure(1,weight=1);ttk.Button(form,text="Choose notes",command=self.choose_notes).grid(row=2,column=2);ttk.Button(form,text="Choose asset",command=self.choose_asset).grid(row=3,column=2);ttk.Checkbutton(form,text="Draft",variable=self.draft).grid(row=4,column=1,sticky="w");ttk.Checkbutton(form,text="Prerelease",variable=self.prerelease).grid(row=4,column=1,sticky="e");ttk.Button(form,text="Create local annotated tag",command=self.create_tag).grid(row=5,column=0,pady=7);ttk.Button(form,text="Push tag",command=self.push_tag).grid(row=5,column=1,sticky="w");ttk.Button(form,text="Publish GitHub Release",command=self.publish,style="Accent.TButton").grid(row=5,column=1,sticky="e")
        self.summary=tk.Text(self,height=12,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="x",padx=8);self.panel=JobPanel(self,self.jobs);self.panel.pack(fill="both",expand=True,padx=8,pady=8)
    def refresh(self):
        branch=self.git.execute("branch","--show-current").stdout.strip();head=self.git.execute("rev-parse","HEAD").stdout.strip();latest=self.git.execute("describe","--tags","--abbrev=0",check=False).output;self.summary.delete("1.0","end");self.summary.insert("1.0",f"Branch: {branch or 'detached'}\nHEAD: {head}\nLatest tag: {latest}\nWorking tree: {'clean' if self.git.repository_state().clean else 'changed'}")
    def choose_notes(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Markdown","*.md"),("All files","*")]);self.notes.set(p or self.notes.get())
    def choose_asset(self):
        p=filedialog.askopenfilename(parent=self);self.asset.set(p or self.asset.get())
    def start(self,args):self.panel.start(args,self.repo)
    def create_tag(self):
        tag=self.tag.get().strip();title=self.title_var.get().strip() or tag
        if tag and self.git.repository_state().clean and messagebox.askyesno("Tag",f"Create annotated tag {tag} at HEAD?",parent=self):self.start(["git","tag","-a",tag,"-m",title])
    def push_tag(self):
        tag=self.tag.get().strip()
        if tag and messagebox.askyesno("Push tag",f"Push {tag} to origin?",parent=self):self.start(["git","push","origin",f"refs/tags/{tag}"])
    def publish(self):
        tag=self.tag.get().strip();title=self.title_var.get().strip() or tag
        if not tag:return
        args=["gh","release","create",tag,"--title",title]
        if self.notes.get().strip():args += ["--notes-file",self.notes.get().strip()]
        else:args += ["--generate-notes"]
        if self.draft.get():args.append("--draft")
        if self.prerelease.get():args.append("--prerelease")
        if self.asset.get().strip():args.append(self.asset.get().strip())
        if messagebox.askyesno("Publish release",f"Run GitHub release creation for {tag} in the background?",parent=self):self.start(args)
