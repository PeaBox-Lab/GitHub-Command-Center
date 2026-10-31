from __future__ import annotations
import tkinter as tk
from tkinter import messagebox,ttk
from ...services import GitService
from ...ui.table_layout import ensure_horizontal_scrollbar

class ChangesCenterV2(tk.Toplevel):
    """Extracted daily changes/staging center using GitService."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.rows=[];self.title("Changes");self.geometry("1180x760");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.message=tk.StringVar();
        for text,cmd in (("Refresh",self.refresh),("Stage selected",self.stage),("Unstage selected",self.unstage),("Discard selected",self.discard)):ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        ttk.Entry(bar,textvariable=self.message).pack(side="left",fill="x",expand=True,padx=6);ttk.Button(bar,text="Commit",command=self.commit,style="Accent.TButton").pack(side="left")
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=2);pane.add(right,weight=3)
        self.tree=ttk.Treeview(left,columns=("state","path"),show="headings",selectmode="extended");self.tree.heading("state",text="State");self.tree.heading("path",text="File");self.tree.column("state",width=90);self.tree.column("path",width=500);self.tree.pack(fill="both",expand=True);ensure_horizontal_scrollbar(self.tree,left);self.tree.bind("<<TreeviewSelect>>",lambda e:self.diff())
        self.out=tk.Text(right,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def refresh(self):
        raw=self.git.execute("status","--porcelain=v1").stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if len(line)<4:continue
            path=line[3:].split(" -> ")[-1];row=(line[:2],path);self.rows.append(row);self.tree.insert("","end",iid=str(len(self.rows)-1),values=row)
        if self.rows:self.tree.selection_set(0);self.diff()
    def selected(self):return [self.rows[int(i)][1] for i in self.tree.selection()]
    def stage(self):
        p=self.selected()
        if p:self.git.execute("add","--",*p);self.refresh()
    def unstage(self):
        p=self.selected()
        if p:self.git.execute("restore","--staged","--",*p);self.refresh()
    def discard(self):
        p=self.selected()
        if p and messagebox.askyesno("Discard",f"Discard working-tree changes for {len(p)} selected path(s)?",parent=self):self.git.execute("restore","--worktree","--",*p);self.refresh()
    def commit(self):
        m=self.message.get().strip()
        if not m:return messagebox.showwarning("Commit","Enter a commit message.",parent=self)
        try:messagebox.showinfo("Commit",self.git.text("commit","-m",m),parent=self);self.message.set("");self.refresh()
        except Exception as exc:messagebox.showerror("Commit",str(exc),parent=self)
    def diff(self):
        p=self.selected();result=self.git.execute("diff","--",*p,check=False) if p else self.git.execute("diff",check=False);self.out.delete("1.0","end");self.out.insert("1.0",result.output)
