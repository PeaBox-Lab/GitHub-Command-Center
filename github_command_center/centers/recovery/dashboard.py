from __future__ import annotations
import tkinter as tk
from datetime import datetime
from tkinter import messagebox,simpledialog,ttk
from ...services import GitService
from ...services.recovery_policy import choose_recovery
from ...ui.table_layout import ensure_horizontal_scrollbar

class RecoveryDashboardV2(tk.Toplevel):
    """Extracted recovery dashboard prioritizing non-destructive branch preservation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.rows=[];self.title("Recovery Dashboard");self.geometry("1180x750");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh reflog",command=self.refresh).pack(side="left");ttk.Button(bar,text="Inspect",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Create recovery branch",command=self.recover,style="Accent.TButton").pack(side="left")
        wrap=ttk.Frame(self);wrap.pack(fill="both",expand=True,padx=8,pady=5)
        self.tree=ttk.Treeview(wrap,columns=("index","hash","date","action","subject"),show="headings")
        for c,t,w in (("index","Reflog",90),("hash","Commit",100),("date","Date",180),("action","Action",180),("subject","Subject",520)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);ensure_horizontal_scrollbar(self.tree,wrap)
        self.out=tk.Text(self,height=14,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        raw=self.git.execute("reflog","show","--date=iso-strict","--format=%gd%x1f%H%x1f%cd%x1f%gs","-250",check=False).stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:
                action,subject=(p[3].split(": ",1)+[""])[:2] if ": " in p[3] else (p[3],"");row=(p[0],p[1],p[2],action,subject);self.rows.append(row);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[0],p[1][:10],p[2],action,subject))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        result=self.git.execute("show","--stat","--patch","--find-renames",r[1],check=False);self.out.delete("1.0","end");self.out.insert("1.0",result.output)
    def recover(self):
        r=self.selected()
        if not r:return
        decision=choose_recovery(reflog_available=True,commit_known=True,fsck_candidate=False);default=f"recovery/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{r[1][:8]}";name=simpledialog.askstring("Recovery branch",f"Recommended method: {decision.method}\n{decision.rationale}\n\nBranch name:",initialvalue=default,parent=self)
        if name:
            try:messagebox.showinfo("Recovery",self.git.text("branch",name,r[1]),parent=self);self.refresh()
            except Exception as exc:messagebox.showerror("Recovery",str(exc),parent=self)
