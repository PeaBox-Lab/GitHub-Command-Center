from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import GitService
from ...ui.table_layout import ensure_horizontal_scrollbar

class HistoryCenterV2(tk.Toplevel):
    """Extracted history/commit inspection center using GitService."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.rows=[];self.title("History");self.geometry("1240x780");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.limit=tk.IntVar(value=300);self.query=tk.StringVar();ttk.Label(bar,text="Limit").pack(side="left");ttk.Spinbox(bar,from_=50,to=5000,increment=50,textvariable=self.limit,width=8).pack(side="left",padx=3);ttk.Entry(bar,textvariable=self.query).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);top=ttk.Frame(pane);bottom=ttk.Frame(pane);pane.add(top,weight=3);pane.add(bottom,weight=2)
        self.tree=ttk.Treeview(top,columns=("hash","date","author","refs","subject"),show="headings")
        for c,t,w in (("hash","Commit",100),("date","Date",120),("author","Author",180),("refs","Refs",260),("subject","Subject",520)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);ensure_horizontal_scrollbar(self.tree,top);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(bottom,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def refresh(self):
        args=["log",f"-{int(self.limit.get())}","--all","--date=short","--decorate=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%D%x1f%s"]
        if self.query.get().strip():args += ["--regexp-ignore-case","--grep",self.query.get().strip()]
        raw=self.git.execute(*args).stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[1],p[2],p[3],p[4],p[5]))
        if self.rows:self.tree.selection_set(0);self.inspect()
    def inspect(self):
        s=self.tree.selection()
        if not s:return
        sha=self.rows[int(s[0])][0];result=self.git.execute("show","--stat","--patch","--find-renames",sha,check=False);self.out.delete("1.0","end");self.out.insert("1.0",result.output)
