from __future__ import annotations
import tkinter as tk
from tkinter import messagebox,ttk
from ...services import GitService
from ...ui.table_layout import ensure_horizontal_scrollbar

class BranchDashboardV2(tk.Toplevel):
    """Extracted branch dashboard using GitService rather than the legacy helper."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.rows=[];self.title("Branch Dashboard");self.geometry("1180x740");self._build();self.refresh()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill="x");ttk.Button(b,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(b,text="Switch selected",command=self.switch).pack(side="left",padx=3);ttk.Button(b,text="Compare with current",command=self.compare).pack(side="left")
        wrap=ttk.Frame(self);wrap.pack(fill="both",expand=True,padx=8,pady=5)
        self.tree=ttk.Treeview(wrap,columns=("branch","upstream","ahead","behind","date","subject"),show="headings")
        for c,t,w in (("branch","Branch",230),("upstream","Upstream",250),("ahead","Ahead",70),("behind","Behind",70),("date","Last commit",120),("subject","Subject",420)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);ensure_horizontal_scrollbar(self.tree,wrap)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        raw=self.git.execute("for-each-ref","--sort=-committerdate","--format=%(refname:short)%09%(upstream:short)%09%(committerdate:short)%09%(subject)","refs/heads/").stdout
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3);branch=p[0];up=p[1] if len(p)>1 else "";date=p[2] if len(p)>2 else "";subject=p[3] if len(p)>3 else "";ahead=behind="-"
            if up:
                a=self.git.execute("rev-list","--count",f"{up}..{branch}",check=False);d=self.git.execute("rev-list","--count",f"{branch}..{up}",check=False);ahead=a.stdout.strip() if a.ok else "?";behind=d.stdout.strip() if d.ok else "?"
            row=(branch,up,ahead,behind,date,subject);self.rows.append(row);self.tree.insert("","end",iid=str(len(self.rows)-1),values=row)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def switch(self):
        r=self.selected()
        if not r:return
        try:messagebox.showinfo("Branch",self.git.text("switch",r[0]),parent=self);self.refresh()
        except Exception as exc:messagebox.showerror("Branch",str(exc),parent=self)
    def compare(self):
        r=self.selected()
        if not r:return
        current=self.git.execute("branch","--show-current").stdout.strip()
        result=self.git.execute("log","--left-right","--graph","--oneline",f"{current}...{r[0]}",check=False)
        self.out.delete("1.0","end");self.out.insert("1.0",result.output)
