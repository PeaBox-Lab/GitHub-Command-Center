"""Bounded feature domain for GitHub Command Center v3.74."""
import csv
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ...core.command_gateway import GitError, git
from ...core.process_gateway import run_process, start_process

class GitPathspecCenter(tk.Toplevel):
    """Preview Git pathspec selection before using it in other workflows."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Pathspec Explorer");self.geometry("1020x660");self.spec=tk.StringVar(value="*.py");self._build();self.preview()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Entry(bar,textvariable=self.spec).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Preview tracked matches",command=self.preview).pack(side="left",padx=3);ttk.Button(bar,text="Preview changed matches",command=self.changed).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Examples: *.py, src/**, :(glob)**/*.md, :(exclude)vendor/**. This center is read-only and helps validate pathspec behavior first.",padding=8).pack(fill="x")
    def preview(self):
        s=self.spec.get().strip()
        try:v=git(self.repo,"ls-files","--",s)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def changed(self):
        s=self.spec.get().strip()
        try:v=git(self.repo,"status","--short","--",s)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class GitGrepStudio(tk.Toplevel):
    """Advanced repository grep across the working tree or a historical ref."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Grep Studio");self.geometry("1120x720");self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.query=tk.StringVar();self.ref=tk.StringVar();self.path=tk.StringVar();self.regex=tk.BooleanVar();self.ignorecase=tk.BooleanVar(value=True)
        ttk.Entry(bar,textvariable=self.query).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.ref,width=18).pack(side="left",padx=3);ttk.Entry(bar,textvariable=self.path,width=24).pack(side="left")
        ttk.Checkbutton(bar,text="Regex",variable=self.regex).pack(side="left",padx=4);ttk.Checkbutton(bar,text="Ignore case",variable=self.ignorecase).pack(side="left");ttk.Button(bar,text="Search",command=self.search).pack(side="left",padx=4)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Ref is optional; when supplied, grep searches that historical tree. Pathspec is optional. Matches stay read-only.",padding=8).pack(fill="x")
    def search(self):
        q=self.query.get()
        if not q:return
        args=["grep","-n","-I"]
        if self.ignorecase.get():args.append("-i")
        args += ["-E" if self.regex.get() else "-F",q]
        ref=self.ref.get().strip()
        if ref:args.append(ref)
        p=self.path.get().strip()
        if p:args += ["--",p]
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class ArchiveCompareCenter(tk.Toplevel):
    """Compare repository trees between two refs using name-status and directory summaries."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Tree Comparison Center");self.geometry("1120x730");self._build();self.compare()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.a=tk.StringVar(value="HEAD~1");self.b=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.a,width=24).pack(side="left");ttk.Entry(bar,textvariable=self.b,width=24).pack(side="left",padx=4);ttk.Button(bar,text="Compare trees",command=self.compare).pack(side="left");ttk.Button(bar,text="Export report",command=self.export).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def compare(self):
        a=self.a.get().strip();b=self.b.get().strip()
        try:
            names=git(self.repo,"diff","--name-status","--find-renames",a,b);stat=git(self.repo,"diff","--dirstat=files,0,cumulative",a,b);short=git(self.repo,"diff","--shortstat",a,b)
            self.report=f"TREE COMPARISON\n{'='*72}\n{a} -> {b}\n{short}\n\nDIRECTORY DISTRIBUTION\n{stat}\n\nFILES\n{names}"
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="tree-comparison.txt")
        if p:Path(p).write_text(self.report)

class RemoteUrlAuditCenter(tk.Toplevel):
    """Audit fetch/push URLs independently and safely update them."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote URL Audit");self.geometry("1100x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.fetchurl=tk.StringVar();self.pushurl=tk.StringVar();ttk.Entry(bar,textvariable=self.fetchurl).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.pushurl).pack(side="left",fill="x",expand=True,padx=4);ttk.Button(bar,text="Set selected URLs",command=self.set_urls).pack(side="left");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("remote","fetch","push"),show="headings")
        for c,t,w in [("remote","Remote",150),("fetch","Fetch URL",450),("push","Push URL",450)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<<TreeviewSelect>>",lambda e:self.select())
        ttk.Label(self,text="Useful for read-from-upstream / push-to-fork workflows. Embedded-credential URLs should be replaced with standard SSH or HTTPS URLs.",padding=8).pack(fill="x")
    def refresh(self):
        names=[x for x in git(self.repo,"remote").splitlines() if x and x!="Completed successfully."];self.rows=[];self.tree.delete(*self.tree.get_children())
        for n in names:
            try:f=git(self.repo,"remote","get-url",n)
            except:f=""
            try:p=git(self.repo,"remote","get-url","--push",n)
            except:p=f
            self.rows.append((n,f,p));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(n,f,p))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def select(self):
        r=self.selected()
        if r:self.fetchurl.set(r[1]);self.pushurl.set(r[2])
    def set_urls(self):
        r=self.selected()
        if not r:return
        f=self.fetchurl.get().strip();p=self.pushurl.get().strip()
        if not f or not p:return
        if messagebox.askyesno("Remote URLs",f"Update fetch/push URLs for {r[0]}?",parent=self):
            try:git(self.repo,"remote","set-url",r[0],f);git(self.repo,"remote","set-url","--push",r[0],p);self.refresh()
            except Exception as e:messagebox.showerror("Remote URLs",str(e),parent=self)

class GitReplaceCenter(tk.Toplevel):
    """Inspect and manage git replace refs with guarded creation/deletion."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Replace Center");self.geometry("1080x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.old=tk.StringVar();self.new=tk.StringVar();ttk.Entry(bar,textvariable=self.old).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.new).pack(side="left",fill="x",expand=True,padx=4)
        for t,c in [("Create replace",self.create),("Refresh",self.refresh),("Inspect selected",self.inspect),("Delete selected",self.delete)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("original","replacement"),show="headings");self.tree.heading("original",text="Original object");self.tree.heading("replacement",text="Replacement object");self.tree.column("original",width=480);self.tree.column("replacement",width=480);self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=14,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="git replace changes local object interpretation without rewriting objects. Replace refs are local unless explicitly transferred and should be used deliberately.",padding=8).pack(fill="x")
    def refresh(self):
        try:raw=git(self.repo,"replace","-l")
        except Exception:raw=""
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for orig in [x for x in raw.splitlines() if x and x!="Completed successfully."]:
            try:rep=git(self.repo,"rev-parse",f"refs/replace/{orig}")
            except:rep=""
            self.rows.append((orig,rep));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(orig,rep))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def create(self):
        old=self.old.get().strip();new=self.new.get().strip()
        if not old or not new:return
        try:old=git(self.repo,"rev-parse",old);new=git(self.repo,"rev-parse",new)
        except Exception as e:return messagebox.showerror("Replace",str(e),parent=self)
        if messagebox.askyesno("Create replace ref",f"Locally replace object interpretation:\n{old}\nwith\n{new}?",parent=self):
            try:messagebox.showinfo("Replace",git(self.repo,"replace",old,new),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Replace",str(e),parent=self)
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v="ORIGINAL\n"+git(self.repo,"cat-file","-p",r[0])+"\n\nREPLACEMENT\n"+git(self.repo,"cat-file","-p",r[1])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete(self):
        r=self.selected()
        if r and messagebox.askyesno("Delete replace ref",f"Remove local replace ref for {r[0]}?",parent=self):
            try:messagebox.showinfo("Replace",git(self.repo,"replace","-d",r[0]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Replace",str(e),parent=self)

class MergeBaseExplorer(tk.Toplevel):
    """Explore merge bases, ancestry, fork points and independent tips."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Base Explorer");self.geometry("1040x670");self._build();self.analyze()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.a=tk.StringVar(value="main");self.b=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.a,width=28).pack(side="left");ttk.Entry(bar,textvariable=self.b,width=28).pack(side="left",padx=4)
        for t,c in [("Analyze",self.analyze),("Fork-point",self.forkpoint),("Show independent tips",self.independent)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def show(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def analyze(self):
        a=self.a.get().strip();b=self.b.get().strip()
        try:
            base=git(self.repo,"merge-base",a,b);allb=git(self.repo,"merge-base","--all",a,b);left=git(self.repo,"rev-list","--count",f"{b}..{a}");right=git(self.repo,"rev-list","--count",f"{a}..{b}");
            try:anc=git(self.repo,"merge-base","--is-ancestor",a,b);ancestor="Yes" if anc=="Completed successfully." else "Yes"
            except:ancestor="No"
            v=f"MERGE BASE ANALYSIS\n{'='*72}\nA: {a}\nB: {b}\nPrimary merge base: {base}\nAll merge bases: {allb}\nA-only commits: {left}\nB-only commits: {right}\nIs A ancestor of B: {ancestor}\n\n"+git(self.repo,"show","-s","--oneline","--decorate",base)
        except Exception as e:v=str(e)
        self.show(v)
    def forkpoint(self):
        a=self.a.get().strip();b=self.b.get().strip()
        try:v=git(self.repo,"merge-base","--fork-point",a,b)+"\n\n"+git(self.repo,"log","-1","--oneline",git(self.repo,"merge-base","--fork-point",a,b))
        except Exception as e:v=str(e)
        self.show(v)
    def independent(self):
        try:self.show(git(self.repo,"merge-base","--independent",self.a.get().strip(),self.b.get().strip()))
        except Exception as e:self.show(str(e))

class BranchContainsCenter(tk.Toplevel):
    """Find branches and tags that contain, merged, or point around a selected commit."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Reachability Explorer");self.geometry("1060x690");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.ref=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.ref).pack(side="left",fill="x",expand=True)
        for t,c in [("Analyze",self.run),("Branches containing",self.branches),("Tags containing",self.tags),("Branches not merged",self.notmerged)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def show(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def run(self):
        r=self.ref.get().strip() or "HEAD"
        try:v=git(self.repo,"show","-s","--decorate","--date=iso-strict","--pretty=fuller",r)+"\n\nBRANCHES CONTAINING\n"+git(self.repo,"branch","-a","--contains",r)+"\n\nTAGS CONTAINING\n"+git(self.repo,"tag","--contains",r)
        except Exception as e:v=str(e)
        self.show(v)
    def branches(self):
        try:self.show(git(self.repo,"branch","-a","--contains",self.ref.get().strip() or "HEAD"))
        except Exception as e:self.show(str(e))
    def tags(self):
        try:self.show(git(self.repo,"tag","--contains",self.ref.get().strip() or "HEAD"))
        except Exception as e:self.show(str(e))
    def notmerged(self):
        try:self.show(git(self.repo,"branch","-a","--no-merged",self.ref.get().strip() or "HEAD"))
        except Exception as e:self.show(str(e))

class RevertQueueCenter(tk.Toplevel):
    """Build and execute a protected queue of commits to revert."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Revert Queue Center");self.geometry("1200x760");self.rows=[];self.queue=[];self._build();self.load()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.ref=tk.StringVar(value="--all");ttk.Entry(bar,textvariable=self.ref,width=20).pack(side="left")
        for t,c in [("Load commits",self.load),("Add selected",self.add),("Remove",self.remove),("Move up",lambda:self.move(-1)),("Move down",lambda:self.move(1)),("Execute queue",self.execute),("Continue",lambda:self.control("--continue")),("Abort",lambda:self.control("--abort"))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        ttk.Label(a,text="Available commits",font=("Segoe UI Semibold",10)).pack(anchor="w");self.available=tk.Listbox(a,font=("Consolas",9));self.available.pack(fill="both",expand=True)
        ttk.Label(b,text="Revert order",font=("Segoe UI Semibold",10)).pack(anchor="w");self.queued=tk.Listbox(b,font=("Consolas",9));self.queued.pack(fill="both",expand=True)
        ttk.Label(self,text="Reverts are applied in queue order as new commits. A timestamped recovery branch is created first. Merge commits require a mainline choice and are excluded from this queue.",padding=8).pack(fill="x")
    def load(self):
        args=["log","-300","--no-merges","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%s"]
        if self.ref.get().strip() and self.ref.get().strip()!="--all":args.append(self.ref.get().strip())
        else:args.insert(1,"--all")
        raw=git(self.repo,*args);self.rows=[];self.available.delete(0,"end")
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:self.rows.append(p);self.available.insert("end",f"{p[1]}  {p[2]}  {p[3]}")
    def add(self):
        for i in self.available.curselection():
            if not any(x[0]==self.rows[i][0] for x in self.queue):self.queue.append(self.rows[i])
        self.render()
    def render(self):self.queued.delete(0,"end");[self.queued.insert("end",f"{r[1]}  {r[3]}") for r in self.queue]
    def remove(self):
        for i in reversed(self.queued.curselection()):del self.queue[i]
        self.render()
    def move(self,d):
        s=self.queued.curselection()
        if not s:return
        i=s[0]
        if 0<=i+d<len(self.queue):self.queue[i],self.queue[i+d]=self.queue[i+d],self.queue[i];self.render();self.queued.selection_set(i+d)
    def execute(self):
        import datetime
        if not self.queue:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Revert queue","Commit or stash local changes first.",parent=self)
        if not messagebox.askyesno("Revert queue",f"Create {len(self.queue)} revert commit(s) in the displayed order?",parent=self):return
        backup=f"gccc-backup/pre-revert-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:git(self.repo,"branch",backup);out=git(self.repo,"revert","--no-edit",*[r[0] for r in self.queue]);messagebox.showinfo("Revert queue",f"{out}\n\nBackup: {backup}",parent=self);self.queue=[];self.render()
        except Exception as e:messagebox.showwarning("Revert paused",f"Backup: {backup}\n\n{e}\n\nResolve conflicts, stage them, then Continue or Abort.",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Revert",git(self.repo,"revert",arg),parent=self)
        except Exception as e:messagebox.showerror("Revert",str(e),parent=self)

class GitLogQueryCenter(tk.Toplevel):
    """Compose advanced git log queries from author/date/path/merge filters."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Log Query Builder");self.geometry("1160x740");self._build();self.run()
    def _build(self):
        f=ttk.Frame(self,padding=8);f.pack(fill="x");self.author=tk.StringVar();self.since=tk.StringVar();self.until=tk.StringVar();self.path=tk.StringVar();self.grep=tk.StringVar();self.merges=tk.StringVar(value="All")
        fields=[("Author",self.author),("Since",self.since),("Until",self.until),("Message grep",self.grep),("Path",self.path)]
        for i,(label,var) in enumerate(fields):ttk.Label(f,text=label).grid(row=i//3*2,column=(i%3)*2,sticky="w");ttk.Entry(f,textvariable=var,width=26).grid(row=i//3*2+1,column=(i%3)*2,sticky="ew",padx=(0,8),pady=(0,6))
        ttk.Label(f,text="Merge commits").grid(row=2,column=4,sticky="w");ttk.Combobox(f,textvariable=self.merges,values=["All","Only merges","No merges"],state="readonly",width=18).grid(row=3,column=4,sticky="w")
        for c in (0,2,4):f.columnconfigure(c,weight=1)
        ttk.Button(f,text="Run query",command=self.run,style="Accent.TButton").grid(row=4,column=4,sticky="e",pady=5);ttk.Button(f,text="Export",command=self.export).grid(row=4,column=3,sticky="e")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def args(self):
        args=["log","--all","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s"]
        if self.author.get().strip():args += ["--author",self.author.get().strip()]
        if self.since.get().strip():args += ["--since",self.since.get().strip()]
        if self.until.get().strip():args += ["--until",self.until.get().strip()]
        if self.grep.get().strip():args += ["--regexp-ignore-case","--grep",self.grep.get().strip()]
        if self.merges.get()=="Only merges":args.append("--merges")
        elif self.merges.get()=="No merges":args.append("--no-merges")
        if self.path.get().strip():args += ["--",self.path.get().strip()]
        return args
    def run(self):
        try:self.report=git(self.repo,*self.args())
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="git-log-query.txt")
        if p:Path(p).write_text(self.report)

class IndexInspectorCenter(tk.Toplevel):
    """Inspect index entries, stages, flags and staged blob metadata."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Index Inspector");self.geometry("1180x750");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Inspect staged blob",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Show index flags",command=self.flags).pack(side="left");ttk.Button(bar,text="Unstage selected",command=self.unstage).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("mode","object","stage","path"),show="headings",selectmode="extended")
        for c,t,w in [("mode","Mode",90),("object","Object",330),("stage","Stage",70),("path","Path",620)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(self,height=13,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Index stages 1/2/3 represent merge base/ours/theirs during conflicts. Unstage uses git restore --staged and does not discard working-tree content.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"ls-files","--stage");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if "\t" not in line:continue
            meta,path=line.split("\t",1);p=meta.split()
            if len(p)==3:self.rows.append((p[0],p[1],p[2],path));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
    def selected(self):return [self.rows[int(i)] for i in self.tree.selection()]
    def inspect(self):
        rows=self.selected()
        if not rows:return
        mode,obj,stage,path=rows[0]
        try:v=f"Path: {path}\nMode: {mode}\nObject: {obj}\nStage: {stage}\n\n"+git(self.repo,"cat-file","-p",obj)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def flags(self):
        try:v=git(self.repo,"ls-files","-v")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def unstage(self):
        paths=sorted(set(r[3] for r in self.selected()))
        if paths and messagebox.askyesno("Unstage",f"Unstage {len(paths)} selected path(s)?",parent=self):
            try:messagebox.showinfo("Unstage",git(self.repo,"restore","--staged","--",*paths),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Unstage",str(e),parent=self)
