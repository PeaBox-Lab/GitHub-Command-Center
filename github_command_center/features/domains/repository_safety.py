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

class IgnoreAttributesStudio(tk.Toplevel):
    """Unified editor and tester for .gitignore and .gitattributes."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Ignore & Attributes Studio");self.geometry("1180x760");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar();ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        for text,cmd in [("Test ignore",self.test_ignore),("Check attributes",self.check_attr),("Save files",self.save),("Add Python defaults",self.python_defaults),("Add binary defaults",self.binary_defaults)]:ttk.Button(top,text=text,command=cmd).pack(side="left",padx=2)
        nb=ttk.Notebook(self);nb.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(nb);b=ttk.Frame(nb);c=ttk.Frame(nb);nb.add(a,text=".gitignore");nb.add(b,text=".gitattributes");nb.add(c,text="Test results")
        self.ignore=tk.Text(a,wrap="none",undo=True,font=("Consolas",9));self.ignore.pack(fill="both",expand=True)
        self.attrs=tk.Text(b,wrap="none",undo=True,font=("Consolas",9));self.attrs.pack(fill="both",expand=True)
        self.out=tk.Text(c,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def load(self):
        for widget,name in ((self.ignore,".gitignore"),(self.attrs,".gitattributes")):
            p=Path(self.repo)/name;widget.delete("1.0","end");widget.insert("1.0",p.read_text(encoding="utf-8") if p.exists() else "")
    def save(self):
        (Path(self.repo)/".gitignore").write_text(self.ignore.get("1.0","end-1c")+"\n");(Path(self.repo)/".gitattributes").write_text(self.attrs.get("1.0","end-1c")+"\n");messagebox.showinfo("Ignore & Attributes","Saved both files. Review and stage them when ready.",parent=self)
    def result(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def test_ignore(self):
        p=self.path.get().strip()
        if not p:return
        try:self.result(git(self.repo,"check-ignore","-v","--no-index","--",p))
        except Exception as e:self.result("Path is not ignored, or Git returned:\n"+str(e))
    def check_attr(self):
        p=self.path.get().strip()
        if not p:return
        try:self.result(git(self.repo,"check-attr","-a","--",p))
        except Exception as e:self.result(str(e))
    def append_unique(self,w,text):
        cur=w.get("1.0","end-1c")
        for line in text.splitlines():
            if line and line not in cur.splitlines():w.insert("end",("\n" if w.get("1.0","end-1c") else "")+line)
    def python_defaults(self):self.append_unique(self.ignore,"__pycache__/\n*.py[cod]\n.venv/\nbuild/\ndist/\n*.egg-info/\n.env")
    def binary_defaults(self):self.append_unique(self.attrs,"* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.jpeg binary\n*.gif binary\n*.zip binary\n*.pdf binary")

class WorktreeSafetyCenter(tk.Toplevel):
    """Worktree-aware branch safety and cleanup dashboard."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Worktree Safety Center");self.geometry("1180x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Open selected folder",self.open_folder),("Lock worktree",self.lock),("Unlock worktree",self.unlock),("Prune dry-run",self.prune_preview),("Prune",self.prune)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("path","branch","head","locked","prunable"),show="headings")
        for c,t,w in [("path","Worktree",470),("branch","Branch",240),("head","HEAD",110),("locked","Locked",90),("prunable","Prunable",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Use lock for removable/network drives. Prune removes stale worktree administrative records, not a healthy checked-out worktree.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"worktree","list","--porcelain");self.rows=[];cur={}
        for line in raw.splitlines()+[""]:
            if not line:
                if cur:self.rows.append(cur);cur={}
            elif " " in line:
                k,v=line.split(" ",1);cur[k]=v
            else:cur[line]="true"
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r.get("worktree",""),r.get("branch","").replace("refs/heads/",""),r.get("HEAD","")[:10],"Yes" if "locked" in r else "No","Yes" if "prunable" in r else "No"))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def open_folder(self):
        import os
        r=self.selected()
        if r:
            p=r.get("worktree")
            try:os.startfile(p) if hasattr(os,"startfile") else start_process(["xdg-open",p])
            except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def worktree_cmd(self,action):
        r=self.selected()
        if not r:return
        try:messagebox.showinfo("Worktree",git(self.repo,"worktree",action,r["worktree"]),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def lock(self):self.worktree_cmd("lock")
    def unlock(self):self.worktree_cmd("unlock")
    def prune_preview(self):
        try:messagebox.showinfo("Prune dry-run",git(self.repo,"worktree","prune","--dry-run","--verbose"),parent=self)
        except Exception as e:messagebox.showerror("Prune",str(e),parent=self)
    def prune(self):
        if messagebox.askyesno("Prune worktrees","Remove stale worktree administration records?",parent=self):
            try:messagebox.showinfo("Prune",git(self.repo,"worktree","prune","--verbose"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Prune",str(e),parent=self)

class RepositoryDoctor(tk.Toplevel):
    """Actionable repository diagnosis combining Git state, config and integrity."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Doctor");self.geometry("1120x760");self._build();self.run()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Run diagnosis",command=self.run).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "ERROR: "+str(e)
    def run(self):
        checks=[]
        status=self.safe("status","--porcelain");checks.append(("Working tree",status=="Completed successfully.","Clean" if status=="Completed successfully." else "Local changes exist"))
        branch=self.safe("branch","--show-current");checks.append(("Current branch",bool(branch) and not branch.startswith("ERROR"),branch))
        upstream=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");checks.append(("Upstream",not upstream.startswith("ERROR"),upstream))
        remote=self.safe("remote","get-url","origin");checks.append(("Origin",not remote.startswith("ERROR"),remote))
        fsck=self.safe("fsck","--no-progress");checks.append(("Object integrity",not fsck.startswith("ERROR"),fsck))
        try:conf=git(self.repo,"diff","--name-only","--diff-filter=U");conflict=conf!="Completed successfully." and bool(conf.strip())
        except:conflict=False;conf=""
        checks.append(("Merge conflicts",not conflict,conf if conflict else "None"))
        try:a=git(self.repo,"rev-list","--count","@{u}..HEAD");b=git(self.repo,"rev-list","--count","HEAD..@{u}");sync=f"Ahead {a}, behind {b}";ok=not (a!="0" and b!="0")
        except Exception as e:sync="Unavailable: "+str(e);ok=False
        checks.append(("Sync divergence",ok,sync))
        report="REPOSITORY DOCTOR\n"+"="*78+"\n\n"+"\n\n".join(f"[{'PASS' if ok else 'ATTN'}] {name}\n  {detail}" for name,ok,detail in checks)+"\n\nRECOMMENDED ACTIONS\n"
        for name,ok,detail in checks:
            if not ok:
                advice={"Working tree":"Commit, discard, or stash intentional changes before risky operations.","Upstream":"Publish the branch or configure its upstream.","Origin":"Configure an origin remote.","Object integrity":"Review fsck output before further cleanup.","Merge conflicts":"Open Resolve conflicts.","Sync divergence":"Open Compare, then explicitly merge or rebase."}.get(name,"Review the reported state.");report+=f"- {name}: {advice}\n"
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-doctor.txt")
        if p:Path(p).write_text(self.report)

class TagReleaseAuditCenter(tk.Toplevel):
    """Audit tags for type, target, date, signature and remote presence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Tag & Release Audit");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Verify selected signature",command=self.verify).pack(side="left",padx=3);ttk.Button(top,text="Push selected tag",command=self.push).pack(side="left");ttk.Button(top,text="Open release center",command=lambda:ReleaseCenter(self,self.repo)).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("tag","type","target","date","remote"),show="headings")
        for c,t,w in [("tag","Tag",270),("type","Type",100),("target","Target",110),("date","Tagger/commit date",170),("remote","On origin",100)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        remote=set()
        try:
            r=git(self.repo,"ls-remote","--tags","origin");remote={x.split("refs/tags/",1)[1].replace("^{}","") for x in r.splitlines() if "refs/tags/" in x}
        except:pass
        raw=git(self.repo,"for-each-ref","--sort=-creatordate","--format=%(refname:short)%09%(objecttype)%09%(objectname:short)%09%(creatordate:iso8601)","refs/tags/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3)
            if len(p)==4:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[0],"Annotated" if p[1]=="tag" else "Lightweight",p[2],p[3],"Yes" if p[0] in remote else "No"))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def verify(self):
        t=self.selected()
        if not t:return
        try:v=git(self.repo,"tag","-v",t)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def push(self):
        t=self.selected()
        if t and messagebox.askyesno("Push tag",f"Push {t} to origin?",parent=self):
            try:messagebox.showinfo("Push tag",git(self.repo,"push","origin",f"refs/tags/{t}"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Push tag",str(e),parent=self)

class StashManagerPro(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Stash Manager Pro");self.geometry("1180x760");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.msg=tk.StringVar()
        ttk.Entry(top,textvariable=self.msg).pack(side="left",fill="x",expand=True)
        for t,c in [("Stash tracked",lambda:self.save(False)),("Stash + untracked",lambda:self.save(True)),("Refresh",self.refresh),("Apply",self.apply),("Pop",self.pop),("Create branch",self.branch),("Drop",self.drop)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("stash","date","branch","message"),show="headings")
        for c,t,w in [("stash","Stash",100),("date","Date",170),("branch","Branch/context",230),("message","Message",600)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.text=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
    def refresh(self):
        raw=git(self.repo,"stash","list","--date=iso-strict","--format=%gd%x1f%cd%x1f%gs");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",2)
            if len(p)==3:
                msg=p[2];branch=msg.split(":",1)[0];self.rows.append((p[0],p[1],branch,msg));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def details(self):
        st=self.selected()
        if st:
            try:v=git(self.repo,"stash","show","--stat","--patch",st)
            except Exception as e:v=str(e)
            self.text.delete("1.0","end");self.text.insert("1.0",v)
    def save(self,untracked):
        args=["stash","push"]+(["-u"] if untracked else [])+["-m",self.msg.get().strip() or "GitHub Command Center stash"]
        try:messagebox.showinfo("Stash",git(self.repo,*args),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Stash",str(e),parent=self)
    def action(self,kind):
        st=self.selected()
        if not st:return
        try:messagebox.showinfo("Stash",git(self.repo,"stash",kind,st),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Stash",str(e),parent=self)
    def apply(self):self.action("apply")
    def pop(self):
        st=self.selected()
        if st and messagebox.askyesno("Pop stash",f"Apply and drop {st}?",parent=self):self.action("pop")
    def drop(self):
        st=self.selected()
        if st and messagebox.askyesno("Drop stash",f"Permanently drop {st}?",parent=self):self.action("drop")
    def branch(self):
        st=self.selected()
        if not st:return
        name=simpledialog.askstring("Stash branch","New branch name:",parent=self)
        if name:
            try:messagebox.showinfo("Stash branch",git(self.repo,"stash","branch",name,st),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Stash branch",str(e),parent=self)

class CleanPreviewCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safe Clean Center");self.geometry("1000x660");self.include_ignored=tk.BooleanVar();self.directories=tk.BooleanVar(value=True);self._build();self.preview()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Checkbutton(top,text="Include directories",variable=self.directories,command=self.preview).pack(side="left");ttk.Checkbutton(top,text="Include ignored files",variable=self.include_ignored,command=self.preview).pack(side="left",padx=8);ttk.Button(top,text="Refresh preview",command=self.preview).pack(side="left");ttk.Button(top,text="Clean previewed items",command=self.clean).pack(side="right")
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Cleaning cannot be undone by Git. Ignored files are excluded by default and require an extra typed confirmation when included.",padding=8).pack(fill="x")
    def args(self,dry=True):
        args=["clean",f"-{'n' if dry else 'f'}"]
        if self.directories.get():args.append("-d")
        if self.include_ignored.get():args.append("-x")
        return args
    def preview(self):
        try:v=git(self.repo,*self.args(True))
        except Exception as e:v=str(e)
        self.preview_text=v;self.text.delete("1.0","end");self.text.insert("1.0",v)
    def clean(self):
        self.preview()
        if self.preview_text=="Completed successfully.":return messagebox.showinfo("Clean","Nothing matched the clean rules.",parent=self)
        if self.include_ignored.get():
            typed=simpledialog.askstring("Dangerous clean","Ignored files are included. Type CLEAN IGNORED to continue:",parent=self)
            if typed!="CLEAN IGNORED":return
        elif not messagebox.askyesno("Clean",f"Delete the previewed untracked items?\n\n{self.preview_text[:1600]}",parent=self):return
        try:messagebox.showinfo("Clean",git(self.repo,*self.args(False)),parent=self);self.preview()
        except Exception as e:messagebox.showerror("Clean",str(e),parent=self)

class RepositorySizeCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Size Explorer");self.geometry("1120x740");self._build();self.analyze()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Analyze",command=self.analyze).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def analyze(self):
        import os
        root=Path(self.repo);gitdir=root/".git";tracked=git(self.repo,"ls-files").splitlines();largest=[]
        for f in tracked:
            p=root/f
            try:
                if p.is_file():largest.append((p.stat().st_size,f))
            except OSError:pass
        largest=sorted(largest,reverse=True)[:30]
        def dsize(path):
            total=0
            for base,dirs,files in os.walk(path):
                for n in files:
                    try:total+=(Path(base)/n).stat().st_size
                    except OSError:pass
            return total
        work=sum(x[0] for x in largest) if False else dsize(root)-dsize(gitdir);gitsize=dsize(gitdir);objects=git(self.repo,"count-objects","-vH")
        report=f"REPOSITORY SIZE EXPLORER\n{'='*78}\nWorking tree files: ~{work/1024/1024:.1f} MB\n.git directory: ~{gitsize/1024/1024:.1f} MB\nTracked files: {len(tracked)}\n\nOBJECT DATABASE\n{objects}\n\nLARGEST CURRENT TRACKED FILES\n"
        for size,name in largest:report+=f"{size/1024/1024:9.2f} MB  {name}\n"
        report+="\nLarge current files may be candidates for Git LFS. Removing large blobs from historical commits requires history rewriting and is intentionally not automated here."
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-size-report.txt")
        if p:Path(p).write_text(self.report)

class ForcePushSafetyCenter(tk.Toplevel):
    """Explicit force-with-lease workflow for rewritten branches; never plain --force."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Force-with-Lease Safety Center");self.geometry("1050x690");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Fetch origin",command=self.fetch).pack(side="left",padx=3);ttk.Button(top,text="Push with lease",command=self.push).pack(side="left")
        self.out=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="This center deliberately does not expose plain --force. Use only after intentional rebase/amend and after reviewing divergence.",padding=8,foreground="#b91c1c").pack(fill="x")
    def snapshot(self):
        b=git(self.repo,"branch","--show-current")
        if not b:raise GitError("Detached HEAD cannot be force-pushed here.")
        up=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}")
        ahead=git(self.repo,"rev-list","--count",f"{up}..HEAD");behind=git(self.repo,"rev-list","--count",f"HEAD..{up}")
        local=git(self.repo,"rev-parse","HEAD");remote=git(self.repo,"rev-parse",up)
        return b,up,ahead,behind,local,remote
    def refresh(self):
        try:
            b,up,ahead,behind,local,remote=self.snapshot();v=f"FORCE-WITH-LEASE REVIEW\n{'='*72}\nBranch: {b}\nUpstream: {up}\nAhead: {ahead}\nBehind: {behind}\nLocal HEAD: {local}\nObserved upstream: {remote}\n\nUse only when remote history is intentionally being replaced after rebase/amend. Fetch first so lease information is current."
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","origin","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def push(self):
        try:b,up,ahead,behind,local,remote=self.snapshot()
        except Exception as e:return messagebox.showerror("Force with lease",str(e),parent=self)
        typed=simpledialog.askstring("Force with lease",f"This may rewrite remote history for {up}.\nType the local branch name exactly to continue:\n{b}",parent=self)
        if typed!=b:return
        if not messagebox.askyesno("Final confirmation",f"Push {b} using --force-with-lease?\nObserved upstream commit:\n{remote}",parent=self):return
        try:messagebox.showinfo("Push",git(self.repo,"push","--force-with-lease"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Push",str(e),parent=self)
