from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..services.diff_service import DiffService
from ..ui.diff_widgets import SideBySideDiff


class VisualDiffCenter(tk.Toplevel):
    """Side-by-side, word-aware Git diff with hunk staging/unstaging."""

    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.service = DiffService(repo)
        self.files = []
        self.title("Visual Diff Center")
        self.geometry("1400x850")
        self._build()
        self.refresh()

    def _build(self):
        top = ttk.Frame(self, padding=8);top.pack(fill="x")
        self.mode=tk.StringVar(value="Working tree");self.algorithm=tk.StringVar(value="histogram");self.path=tk.StringVar()
        ttk.Combobox(top,textvariable=self.mode,values=["Working tree","Staged"],state="readonly",width=16).pack(side="left")
        ttk.Combobox(top,textvariable=self.algorithm,values=["myers","minimal","patience","histogram"],state="readonly",width=12).pack(side="left",padx=4)
        ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left",padx=4)
        ttk.Button(top,text="Stage hunk",command=self.stage_hunk).pack(side="left")
        ttk.Button(top,text="Unstage hunk",command=self.unstage_hunk).pack(side="left",padx=4)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=1);pane.add(right,weight=5)
        self.file_list=tk.Listbox(left,font=("Consolas",9));self.file_list.pack(fill="both",expand=True);self.file_list.bind("<<ListboxSelect>>",lambda e:self.select_file())
        self.hunks=tk.Listbox(left,height=12,font=("Consolas",8));self.hunks.pack(fill="x",pady=(5,0));self.hunks.bind("<<ListboxSelect>>",lambda e:self.select_hunk())
        self.diff=SideBySideDiff(right);self.diff.pack(fill="both",expand=True)
        self.status=tk.StringVar(value="Ready");ttk.Label(self,textvariable=self.status,padding=8).pack(fill="x")

    def refresh(self):
        staged=self.mode.get()=="Staged"
        try:self.files=self.service.files(staged=staged,path=self.path.get().strip(),algorithm=self.algorithm.get())
        except Exception as exc:messagebox.showerror("Visual diff",str(exc),parent=self);return
        self.file_list.delete(0,"end")
        for file in self.files:self.file_list.insert("end",f"{file.status} {file.path}  +{file.additions}/-{file.deletions}")
        self.hunks.delete(0,"end");self.diff.clear();self.status.set(f"{len(self.files)} changed file(s)")
        if self.files:self.file_list.selection_set(0);self.select_file()

    def selected_file(self):
        selection=self.file_list.curselection();return self.files[selection[0]] if selection else None
    def selected_hunk(self):
        file=self.selected_file();selection=self.hunks.curselection();return file.hunks[selection[0]] if file and selection else None
    def select_file(self):
        file=self.selected_file()
        if not file:return
        self.diff.render(file);self.hunks.delete(0,"end")
        for i,hunk in enumerate(file.hunks,1):self.hunks.insert("end",f"H{i} {hunk.header}")
        self.status.set(f"{file.path}: +{file.additions}/-{file.deletions}, {len(file.hunks)} hunk(s)")
        if file.hunks:self.hunks.selection_set(0)
    def select_hunk(self):
        file=self.selected_file();hunk=self.selected_hunk()
        if file and hunk:
            clone=type(file)(path=file.path,old_path=file.old_path,status=file.status,binary=file.binary,hunks=[hunk]);self.diff.render(clone)
    def stage_hunk(self):
        if self.mode.get()=="Staged":return messagebox.showinfo("Visual diff","Switch to Working tree to stage a hunk.",parent=self)
        self._apply(False)
    def unstage_hunk(self):
        if self.mode.get()!="Staged":return messagebox.showinfo("Visual diff","Switch to Staged to unstage a hunk.",parent=self)
        self._apply(True)
    def _apply(self,reverse):
        file=self.selected_file();hunk=self.selected_hunk()
        if not file or not hunk:return
        action="Unstage" if reverse else "Stage"
        if not messagebox.askyesno(action,f"{action} selected hunk in {file.path}?",parent=self):return
        try:self.service.apply_patch(self.service.hunk_patch(file,hunk),cached=True,reverse=reverse);self.refresh()
        except Exception as exc:messagebox.showerror(action,str(exc),parent=self)
