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

class ConfigSnapshotCompareCenter(tk.Toplevel):
    """Capture and compare effective Git configuration snapshots."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Config Snapshot Compare");self.geometry("1120x720");self.before=None;self._build();self.capture()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Capture baseline",command=self.capture).pack(side="left");ttk.Button(bar,text="Compare current",command=self.compare).pack(side="left",padx=3);ttk.Button(bar,text="Export comparison",command=self.export).pack(side="left");ttk.Button(bar,text="Open Config Center",command=lambda:GitConfigCenter(self,self.repo)).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Snapshots include scope and origin. Sensitive values may appear in Git config; review before exporting or sharing the report.",padding=8).pack(fill="x")
    def snapshot(self):
        raw=git(self.repo,"config","--list","--show-origin","--show-scope","--includes");return raw.splitlines()
    def capture(self):
        try:self.before=self.snapshot();self.report="BASELINE CONFIG SNAPSHOT\n"+"="*72+"\n"+"\n".join(self.before)
        except Exception as e:self.before=[];self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def compare(self):
        import difflib
        if self.before is None:self.capture()
        try:current=self.snapshot();diff=list(difflib.unified_diff(self.before,current,fromfile="baseline",tofile="current",lineterm=""));self.report="CONFIG SNAPSHOT COMPARISON\n"+"="*72+"\n"+("\n".join(diff) if diff else "No effective configuration changes detected.")
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="git-config-comparison.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class CommitFixupCenter(tk.Toplevel):
    """Create fixup/squash commits against a selected historical commit."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Fixup & Squash Commit Center");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.mode=tk.StringVar(value="fixup");self.limit=tk.IntVar(value=100)
        ttk.Combobox(bar,textvariable=self.mode,values=["fixup","squash","amend"],state="readonly",width=12).pack(side="left");ttk.Spinbox(bar,from_=20,to=1000,increment=20,textvariable=self.limit,width=8).pack(side="left",padx=4)
        for text,cmd in [("Refresh",self.refresh),("Create from staged changes",self.create),("Open Interactive Rebase",lambda:InteractiveRebaseEditor(self,self.repo))]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("hash","date","author","subject"),show="headings")
        for c,t,w in [("hash","Commit",100),("date","Date",110),("author","Author",190),("subject","Subject",650)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(self,height=13,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Requires staged changes. Fixup/squash commits are intended for later autosquash rebase; amend rewrites HEAD and creates a safety branch first.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"log",f"-{int(self.limit.get())}","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%s");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",4)
            if len(p)==5:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[1],p[2],p[3],p[4]))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--oneline",r[0])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def staged(self):return git(self.repo,"diff","--cached","--name-only")!="Completed successfully."
    def create(self):
        import datetime
        r=self.selected();mode=self.mode.get()
        if not r:return
        if not self.staged():return messagebox.showwarning("Commit","Stage the intended changes first.",parent=self)
        try:
            if mode=="fixup":out=git(self.repo,"commit",f"--fixup={r[0]}")
            elif mode=="squash":out=git(self.repo,"commit",f"--squash={r[0]}")
            else:
                if r[0]!=git(self.repo,"rev-parse","HEAD"):return messagebox.showwarning("Amend","Amend is limited to HEAD. Select the latest commit.",parent=self)
                backup=f"gccc-backup/pre-amend-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}";git(self.repo,"branch",backup)
                if not messagebox.askyesno("Amend",f"Safety branch created: {backup}\n\nAmend HEAD with staged changes while keeping the message?",parent=self):return
                out=git(self.repo,"commit","--amend","--no-edit")
            messagebox.showinfo("Commit",out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Commit",str(e),parent=self)

class TrackedFileFlagsCenter(tk.Toplevel):
    """Inspect and safely manage assume-unchanged and skip-worktree flags."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Tracked File Flags Center");self.geometry("1120x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for text,cmd in [("Refresh",self.refresh),("Set assume-unchanged",lambda:self.setflag("--assume-unchanged")),("Clear assume-unchanged",lambda:self.setflag("--no-assume-unchanged")),("Set skip-worktree",lambda:self.setflag("--skip-worktree")),("Clear skip-worktree",lambda:self.setflag("--no-skip-worktree"))]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("flag","path"),show="headings",selectmode="extended");self.tree.heading("flag",text="Index flag");self.tree.heading("path",text="Tracked path");self.tree.column("flag",width=120);self.tree.column("path",width=900);self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=11,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="These flags are local index hints, not ignore rules. skip-worktree is primarily for sparse workflows; assume-unchanged is an optimization hint and can hide local modifications from normal status views.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"ls-files","-v");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if len(line)>2:self.rows.append((line[0],line[2:]));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
        flagged=[r for r in self.rows if r[0] not in ("H","")];self.out.delete("1.0","end");self.out.insert("1.0",f"Tracked paths: {len(self.rows)}\nNon-default/interesting flags: {len(flagged)}\n\nSelect paths carefully before changing local index flags.")
    def selected(self):return [self.rows[int(i)][1] for i in self.tree.selection()]
    def setflag(self,flag):
        paths=self.selected()
        if not paths:return
        if not messagebox.askyesno("Tracked file flags",f"Apply {flag} to {len(paths)} selected path(s)?",parent=self):return
        try:messagebox.showinfo("Tracked file flags",git(self.repo,"update-index",flag,"--",*paths),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Tracked file flags",str(e),parent=self)

class RevisionWalkCenter(tk.Toplevel):
    """Compose revision walks with first-parent, ancestry-path, topo/date order and boundary flags."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Revision Walk Lab");self.geometry("1120x720");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.spec=tk.StringVar(value="HEAD~20..HEAD");self.order=tk.StringVar(value="--topo-order");self.first=tk.BooleanVar();self.ancestry=tk.BooleanVar();self.boundary=tk.BooleanVar()
        ttk.Entry(bar,textvariable=self.spec).pack(side="left",fill="x",expand=True);ttk.Combobox(bar,textvariable=self.order,values=["--topo-order","--date-order","--author-date-order"],state="readonly",width=19).pack(side="left",padx=4);ttk.Checkbutton(bar,text="First parent",variable=self.first).pack(side="left");ttk.Checkbutton(bar,text="Ancestry path",variable=self.ancestry).pack(side="left",padx=3);ttk.Checkbutton(bar,text="Boundary",variable=self.boundary).pack(side="left");ttk.Button(bar,text="Run",command=self.run).pack(side="left",padx=4)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Revision walks help explain topology. Ancestry-path is meaningful for a commit range such as A..B.",padding=8).pack(fill="x")
    def run(self):
        args=["log","--graph","--decorate","--oneline",self.order.get()]
        if self.first.get():args.append("--first-parent")
        if self.ancestry.get():args.append("--ancestry-path")
        if self.boundary.get():args.append("--boundary")
        args.append(self.spec.get().strip() or "HEAD")
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class GitShowBranchCenter(tk.Toplevel):
    """Visualize branch relationships with git show-branch."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Show-Branch Explorer");self.geometry("1120x720");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.refs=tk.StringVar(value="--all");self.more=tk.IntVar(value=20)
        ttk.Entry(bar,textvariable=self.refs).pack(side="left",fill="x",expand=True);ttk.Label(bar,text="More").pack(side="left",padx=(8,2));ttk.Spinbox(bar,from_=0,to=500,textvariable=self.more,width=7).pack(side="left")
        ttk.Button(bar,text="Run",command=self.run).pack(side="left",padx=4);ttk.Button(bar,text="Export",command=self.export).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Enter --all or space-separated refs. show-branch provides a compact topology comparison across multiple branch tips.",padding=8).pack(fill="x")
    def run(self):
        import shlex
        args=["show-branch",f"--more={int(self.more.get())}"]+shlex.split(self.refs.get().strip() or "--all")
        try:self.report=git(self.repo,*args)
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="show-branch.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class GitNameRevCenter(tk.Toplevel):
    """Assign human-readable ref-relative names to object IDs and revisions."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Name-Rev Explorer");self.geometry("1030x660");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.objects=tk.StringVar(value="HEAD");self.tags=tk.BooleanVar();self.always=tk.BooleanVar(value=True)
        ttk.Entry(bar,textvariable=self.objects).pack(side="left",fill="x",expand=True);ttk.Checkbutton(bar,text="Tags only",variable=self.tags).pack(side="left",padx=4);ttk.Checkbutton(bar,text="Always",variable=self.always).pack(side="left");ttk.Button(bar,text="Resolve names",command=self.run).pack(side="left",padx=4);ttk.Button(bar,text="All reachable",command=self.all).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def args(self):
        import shlex
        args=["name-rev"]
        if self.tags.get():args.append("--tags")
        if self.always.get():args.append("--always")
        return args+shlex.split(self.objects.get().strip() or "HEAD")
    def run(self):
        try:v=git(self.repo,*self.args())
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def all(self):
        args=["name-rev","--all"]
        if self.tags.get():args.append("--tags")
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class GitCountObjectsTrendCenter(tk.Toplevel):
    """Capture local object-database size snapshots and compare growth over time."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-object-trends.json";self.title("Object Growth Tracker");self.geometry("1080x700");self._build();self.load();self.capture()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Capture snapshot",command=self.capture).pack(side="left");ttk.Button(bar,text="Clear history",command=self.clear).pack(side="left",padx=3);ttk.Button(bar,text="Export CSV",command=self.export).pack(side="left");ttk.Button(bar,text="Open Maintenance",command=lambda:MaintenanceCenter(self,self.repo)).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("time","count","size","inpack","packs","sizepack","garbage"),show="headings")
        for c,t,w in [("time","Captured",180),("count","Loose",80),("size","Loose size",100),("inpack","In packs",90),("packs","Packs",70),("sizepack","Pack size",100),("garbage","Garbage",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def load(self):
        import json
        try:self.rows=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        except:self.rows=[]
    def save(self):
        import json
        self.path.write_text(json.dumps(self.rows,indent=2),encoding="utf-8")
    def parse(self,raw):
        d={}
        for line in raw.splitlines():
            if ": " in line:
                k,v=line.split(": ",1);d[k]=v
        return d
    def capture(self):
        import datetime
        try:d=self.parse(git(self.repo,"count-objects","-vH"));d["captured"]=datetime.datetime.now().isoformat(timespec="seconds");self.rows.append(d);self.save();self.render()
        except Exception as e:messagebox.showerror("Object growth",str(e),parent=self)
    def render(self):
        self.tree.delete(*self.tree.get_children())
        for r in self.rows:self.tree.insert("","end",values=(r.get("captured"),r.get("count"),r.get("size"),r.get("in-pack"),r.get("packs"),r.get("size-pack"),r.get("garbage")))
        if len(self.rows)>=2:
            a,b=self.rows[-2],self.rows[-1];v=f"Latest snapshot: {b.get('captured')}\nPrevious snapshot: {a.get('captured')}\n\nLoose objects: {a.get('count')} -> {b.get('count')}\nPacked objects: {a.get('in-pack')} -> {b.get('in-pack')}\nPack size: {a.get('size-pack')} -> {b.get('size-pack')}\nGarbage: {a.get('garbage')} -> {b.get('garbage')}"
        else:v="Capture at least two snapshots to compare object-database growth."
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def clear(self):
        if messagebox.askyesno("Object growth","Clear local object-growth snapshots?",parent=self):self.rows=[];self.save();self.render()
    def export(self):
        import csv
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",initialfile="object-growth.csv")
        if p:
            keys=["captured","count","size","in-pack","packs","size-pack","prune-packable","garbage","size-garbage"]
            with open(p,"w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r.get(k,"") for k in keys} for r in self.rows)

class GitVerifyRefCenter(tk.Toplevel):
    """Resolve and verify refs safely, including symbolic refs and peeling."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Ref Verification Center");self.geometry("1040x680");self.ref=tk.StringVar(value="HEAD");self._build();self.inspect()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Entry(bar,textvariable=self.ref).pack(side="left",fill="x",expand=True)
        for text,cmd in [("Inspect",self.inspect),("Peel to commit",self.peel),("Show symbolic ref",self.symbolic),("Reflog exists?",self.reflog)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Read-only verification using rev-parse, show-ref and symbolic-ref. Useful before scripts or destructive operations that depend on an exact ref.",padding=8).pack(fill="x")
    def show(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def inspect(self):
        r=self.ref.get().strip() or "HEAD"
        try:v=f"REF VERIFICATION\n{'='*72}\nInput: {r}\nResolved: {git(self.repo,'rev-parse','--verify',r)}\nType: {git(self.repo,'cat-file','-t',r)}\n\nMATCHING REFS\n{git(self.repo,'show-ref',r)}"
        except Exception as e:v=str(e)
        self.show(v)
    def peel(self):
        r=self.ref.get().strip() or "HEAD"
        try:self.show(f"Commit: {git(self.repo,'rev-parse','--verify',f'{r}^{{commit}}')}\nPeeled object: {git(self.repo,'rev-parse',f'{r}^{{}}')}")
        except Exception as e:self.show(str(e))
    def symbolic(self):
        r=self.ref.get().strip() or "HEAD"
        try:self.show(git(self.repo,"symbolic-ref","-q",r))
        except Exception as e:self.show("Not a symbolic ref or unavailable.\n\n"+str(e))
    def reflog(self):
        r=self.ref.get().strip() or "HEAD"
        try:self.show(git(self.repo,"reflog","show","-10",r))
        except Exception as e:self.show("No reflog found or unavailable.\n\n"+str(e))

class GitCheckIgnoreBatchCenter(tk.Toplevel):
    """Batch-test ignore rules for many paths with verbose provenance."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Ignore Rule Batch Tester");self.geometry("1080x700");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Test paths",command=self.test).pack(side="left");ttk.Button(top,text="Load untracked paths",command=self.untracked).pack(side="left",padx=3);ttk.Button(top,text="Open Ignore Studio",command=lambda:IgnoreAttributesStudio(self,self.repo)).pack(side="left")
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.input=tk.Text(a,wrap="none",font=("Consolas",9));self.input.pack(fill="both",expand=True)
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="One repository-relative path per line. Verbose output identifies the ignore file, rule line, and matching pattern.",padding=8).pack(fill="x")
    def paths(self):return [x.strip() for x in self.input.get("1.0","end-1c").splitlines() if x.strip()]
    def untracked(self):
        try:raw=git(self.repo,"ls-files","--others","--exclude-standard")
        except Exception as e:raw=str(e)
        self.input.delete("1.0","end");self.input.insert("1.0",raw)
    def test(self):
        paths=self.paths();lines=[]
        for p in paths:
            try:v=git(self.repo,"check-ignore","-v","--no-index","--",p);lines.append(f"{p}\n  {v}")
            except Exception:lines.append(f"{p}\n  NOT IGNORED")
        self.out.delete("1.0","end");self.out.insert("1.0","\n\n".join(lines))
