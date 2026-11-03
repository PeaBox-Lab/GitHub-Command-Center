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

class CherryPickQueueCenter(tk.Toplevel):
    """Build and execute an ordered multi-commit cherry-pick queue with backup protection."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Cherry-Pick Queue Center");self.geometry("1200x760");self.rows=[];self.queue=[];self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.ref=tk.StringVar(value="--all");ttk.Entry(top,textvariable=self.ref,width=24).pack(side="left")
        for t,c in [("Load commits",self.load),("Add selected",self.add),("Remove",self.remove),("Move up",lambda:self.move(-1)),("Move down",lambda:self.move(1)),("Execute queue",self.execute),("Continue",lambda:self.control("--continue")),("Abort",lambda:self.control("--abort"))]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        ttk.Label(a,text="Available commits",font=("Segoe UI Semibold",10)).pack(anchor="w");self.available=tk.Listbox(a,font=("Consolas",9));self.available.pack(fill="both",expand=True)
        ttk.Label(b,text="Ordered queue",font=("Segoe UI Semibold",10)).pack(anchor="w");self.queued=tk.Listbox(b,font=("Consolas",9));self.queued.pack(fill="both",expand=True)
        ttk.Label(self,text="A timestamped pre-cherry-pick backup branch is created before execution. The queue stops on the first conflict.",padding=8).pack(fill="x")
    def load(self):
        args=["log","-250","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%s"]
        if self.ref.get().strip() and self.ref.get().strip()!="--all":args.append(self.ref.get().strip())
        else:args.insert(1,"--all")
        raw=git(self.repo,*args);self.rows=[];self.available.delete(0,"end")
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:self.rows.append(p);self.available.insert("end",f"{p[1]}  {p[2]}  {p[3]}")
    def add(self):
        for i in self.available.curselection():
            r=self.rows[i]
            if not any(x[0]==r[0] for x in self.queue):self.queue.append(r)
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
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Cherry-pick queue","Commit or stash local changes first.",parent=self)
        if not messagebox.askyesno("Cherry-pick queue",f"Apply {len(self.queue)} commits in the displayed order?",parent=self):return
        backup=f"gccc-backup/pre-cherry-pick-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:git(self.repo,"branch",backup);out=git(self.repo,"cherry-pick",*[r[0] for r in self.queue]);messagebox.showinfo("Cherry-pick queue",f"{out}\n\nBackup: {backup}",parent=self);self.queue=[];self.render()
        except Exception as e:messagebox.showwarning("Cherry-pick paused",f"Backup: {backup}\n\n{e}\n\nResolve conflicts and Continue, or Abort.",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Cherry-pick",git(self.repo,"cherry-pick",arg),parent=self)
        except Exception as e:messagebox.showerror("Cherry-pick",str(e),parent=self)

class ReleaseAssetIntegrityCenter(tk.Toplevel):
    """Generate and verify SHA-256 manifests for release assets."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Asset Integrity");self.geometry("1080x700");self.files=[];self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Add assets",self.add),("Clear",self.clear),("Generate SHA256SUMS",self.generate),("Verify manifest",self.verify)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.list=tk.Listbox(self,font=("Consolas",9));self.list.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=15,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def add(self):
        for p in filedialog.askopenfilenames(parent=self):
            if p not in self.files:self.files.append(p)
        self.render()
    def clear(self):self.files=[];self.render();self.out.delete("1.0","end")
    def render(self):self.list.delete(0,"end");[self.list.insert("end",p) for p in self.files]
    def digest(self,p):
        import hashlib
        h=hashlib.sha256()
        with open(p,"rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
        return h.hexdigest()
    def generate(self):
        if not self.files:return
        lines=[f"{self.digest(p)}  {Path(p).name}" for p in self.files];self.out.delete("1.0","end");self.out.insert("1.0","\n".join(lines))
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="SHA256SUMS.txt")
        if target:Path(target).write_text("\n".join(lines)+"\n");messagebox.showinfo("Integrity",f"Saved {target}",parent=self)
    def verify(self):
        manifest=filedialog.askopenfilename(parent=self,filetypes=[("Checksum manifests","*.txt *.sha256"),("All files","*")])
        if not manifest:return
        base=Path(manifest).parent;results=[]
        for line in Path(manifest).read_text(encoding="utf-8").splitlines():
            if not line.strip():continue
            parts=line.split(None,1)
            if len(parts)!=2:results.append(f"INVALID LINE: {line}");continue
            expected,name=parts[0],parts[1].lstrip(" *");p=base/name
            if not p.exists():results.append(f"MISSING  {name}")
            else:results.append(f"{'PASS' if self.digest(p).lower()==expected.lower() else 'FAIL'}  {name}")
        self.out.delete("1.0","end");self.out.insert("1.0","\n".join(results))

class LocalReleaseArchiveCenter(tk.Toplevel):
    """Create a structured local release folder with source, bundle, checksums and notes."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Local Release Archive");self.geometry("960x620");self.version=tk.StringVar();self._build()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);ttk.Label(f,text="Version/tag").grid(row=0,column=0,sticky="w");ttk.Entry(f,textvariable=self.version).grid(row=0,column=1,sticky="ew",padx=8);f.columnconfigure(1,weight=1)
        ttk.Label(f,text="Creates source ZIP, full Git bundle, SHA256SUMS, release notes copy and metadata in a new local folder.",wraplength=760).grid(row=1,column=0,columnspan=2,sticky="w",pady=10)
        ttk.Button(f,text="Build local release archive",command=self.build,style="Accent.TButton").grid(row=2,column=1,sticky="e",pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=3,column=0,columnspan=2,sticky="nsew");f.rowconfigure(3,weight=1)
    def build(self):
        import json,hashlib,datetime,shutil
        version=self.version.get().strip()
        if not version:return messagebox.showwarning("Release archive","Enter a version or tag.",parent=self)
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Release archive","Commit or stash local changes first.",parent=self)
        parent=filedialog.askdirectory(parent=self,title="Choose release archive parent")
        if not parent:return
        folder=Path(parent)/f"{Path(self.repo).name}-{version}";folder.mkdir(parents=True,exist_ok=False)
        zipfile=folder/f"{Path(self.repo).name}-{version}-source.zip";bundle=folder/f"{Path(self.repo).name}-{version}.bundle"
        try:
            git(self.repo,"archive","--format=zip",f"--output={zipfile}","HEAD");git(self.repo,"bundle","create",str(bundle),"--all")
            notes=Path(self.repo)/"RELEASE_NOTES.md"
            if notes.exists():shutil.copy2(notes,folder/"RELEASE_NOTES.md")
            def sha(p):
                h=hashlib.sha256()
                with open(p,"rb") as f:
                    for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
                return h.hexdigest()
            assets=[zipfile,bundle]+(([folder/"RELEASE_NOTES.md"]) if (folder/"RELEASE_NOTES.md").exists() else [])
            (folder/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.name}" for p in assets)+"\n")
            metadata={"repository":Path(self.repo).name,"version":version,"created":datetime.datetime.now().isoformat(),"head":git(self.repo,"rev-parse","HEAD"),"branch":git(self.repo,"branch","--show-current")};(folder/"release-metadata.json").write_text(json.dumps(metadata,indent=2))
            self.out.delete("1.0","end");self.out.insert("1.0",f"Release archive created:\n{folder}\n\n"+"\n".join(p.name for p in folder.iterdir()));messagebox.showinfo("Release archive",f"Created {folder}",parent=self)
        except Exception as e:messagebox.showerror("Release archive",str(e),parent=self)

class CommitSignatureAuditCenter(tk.Toplevel):
    """Audit recent commit and tag signature status without changing repository history."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Signature Audit Center");self.geometry("1180x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.limit=tk.IntVar(value=100);ttk.Label(top,text="Commits").pack(side="left");ttk.Spinbox(top,from_=10,to=1000,increment=10,textvariable=self.limit,width=8).pack(side="left",padx=4);ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export audit",command=self.export).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("hash","date","author","sig","subject"),show="headings")
        for c,t,w in [("hash","Commit",100),("date","Date",110),("author","Author",190),("sig","Signature",115),("subject","Subject",570)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8));self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
    def refresh(self):
        n=max(10,int(self.limit.get()));raw=git(self.repo,"log",f"-{n}","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%G?%x1f%s");self.rows=[];self.tree.delete(*self.tree.get_children())
        labels={"G":"Good","B":"Bad","U":"Good/unknown trust","X":"Expired","Y":"Expired key","R":"Revoked key","E":"Cannot check","N":"Unsigned"}
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[1],p[2],p[3],labels.get(p[4],p[4]),p[5]))
        counts={}
        for r in self.rows:counts[r[4]]=counts.get(r[4],0)+1
        self.report=f"SIGNATURE AUDIT\n{'='*72}\nCommits reviewed: {len(self.rows)}\n"+"\n".join(f"{labels.get(k,k)}: {v}" for k,v in sorted(counts.items()))
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def details(self):
        s=self.tree.selection()
        if not s:return
        try:v=git(self.repo,"show","-s","--show-signature","--date=iso-strict","--pretty=fuller",self.rows[int(s[0])][0])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="signature-audit.txt")
        if p:Path(p).write_text(self.report)

class ReleaseCompareCenter(tk.Toplevel):
    """Compare two release refs with commits, files and compact release statistics."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Comparison Center");self.geometry("1200x760");self._build();self.load_refs()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.old=tk.StringVar();self.new=tk.StringVar(value="HEAD");self.oldbox=ttk.Combobox(top,textvariable=self.old,width=26);self.newbox=ttk.Combobox(top,textvariable=self.new,width=26);self.oldbox.pack(side="left");self.newbox.pack(side="left",padx=4);ttk.Button(top,text="Compare",command=self.compare).pack(side="left");ttk.Button(top,text="Export Markdown",command=self.export).pack(side="left",padx=3)
        nb=ttk.Notebook(self);nb.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(nb);b=ttk.Frame(nb);c=ttk.Frame(nb);nb.add(a,text="Summary");nb.add(b,text="Commits");nb.add(c,text="Files")
        self.summary=tk.Text(a,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="both",expand=True);self.commits=tk.Text(b,wrap="none",font=("Consolas",9));self.commits.pack(fill="both",expand=True);self.files=tk.Text(c,wrap="none",font=("Consolas",9));self.files.pack(fill="both",expand=True)
    def load_refs(self):
        raw=git(self.repo,"tag","--sort=-version:refname");tags=[x for x in raw.splitlines() if x and x!="Completed successfully."];vals=tags+["HEAD"];self.oldbox["values"]=vals;self.newbox["values"]=vals
        if tags:self.old.set(tags[1] if len(tags)>1 else tags[0]);self.new.set(tags[0])
    def compare(self):
        a=self.old.get().strip();b=self.new.get().strip()
        if not a or not b:return
        try:
            count=git(self.repo,"rev-list","--count",f"{a}..{b}");short=git(self.repo,"diff","--shortstat",a,b);stat=git(self.repo,"diff","--stat",a,b);commits=git(self.repo,"log","--date=short","--pretty=format:- %h %ad %an: %s",f"{a}..{b}");files=git(self.repo,"diff","--name-status",a,b)
            self.md=f"# Release comparison: {a} -> {b}\n\n- Commits: {count}\n- Diff: {short}\n\n## Commits\n{commits}\n\n## Files\n```text\n{files}\n```\n"
            self.summary.delete("1.0","end");self.summary.insert("1.0",f"RELEASE COMPARISON\n{'='*72}\n{a} -> {b}\nCommits: {count}\n{short}\n\n{stat}");self.commits.delete("1.0","end");self.commits.insert("1.0",commits);self.files.delete("1.0","end");self.files.insert("1.0",files)
        except Exception as e:messagebox.showerror("Release comparison",str(e),parent=self)
    def export(self):
        if not hasattr(self,"md"):self.compare()
        if not hasattr(self,"md"):return
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="release-comparison.md")
        if p:Path(p).write_text(self.md)

class SafeDeleteBranchWizard(tk.Toplevel):
    """Branch deletion wizard that checks merge, worktree and upstream state first."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safe Branch Delete Wizard");self.geometry("1050x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Delete selected local branch",command=self.delete).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("branch","merged","worktree","upstream","ahead","behind"),show="headings")
        for c,t,w in [("branch","Branch",280),("merged","Merged",80),("worktree","In worktree",100),("upstream","Upstream",270),("ahead","Ahead",70),("behind","Behind",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=10,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8));self.tree.bind("<<TreeviewSelect>>",lambda e:self.assess())
    def refresh(self):
        current=git(self.repo,"branch","--show-current");merged=set(x.strip().lstrip("* ") for x in git(self.repo,"branch","--merged").splitlines());wt=git(self.repo,"worktree","list","--porcelain");used={x.replace("branch refs/heads/","",1) for x in wt.splitlines() if x.startswith("branch refs/heads/")};raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(upstream:short)","refs/heads/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",1);b=p[0];up=p[1] if len(p)>1 else "";ahead=behind="-"
            if up:
                try:ahead=git(self.repo,"rev-list","--count",f"{up}..{b}");behind=git(self.repo,"rev-list","--count",f"{b}..{up}")
                except:pass
            r=dict(branch=b,merged=b in merged,used=b in used,current=b==current,up=up,ahead=ahead,behind=behind);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(b,"Yes" if r["merged"] else "No","Yes" if r["used"] else "No",up or "-",ahead,behind))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def assess(self):
        r=self.selected()
        if not r:return
        blockers=[]
        if r["current"]:blockers.append("This is the current branch.")
        if r["used"]:blockers.append("The branch is checked out in a worktree.")
        if not r["merged"]:blockers.append("Git does not report the branch as merged into the current branch.")
        if str(r["ahead"]) not in ("0","-"):blockers.append(f"Branch has {r['ahead']} commit(s) not present in its configured upstream.")
        v=f"BRANCH DELETE ASSESSMENT\n{'='*72}\nBranch: {r['branch']}\nUpstream: {r['up'] or 'None'}\n\n"+("SAFE FOR NORMAL DELETE (-d)" if not blockers else "BLOCKED\n- "+"\n- ".join(blockers))
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete(self):
        r=self.selected()
        if not r:return
        if r["current"] or r["used"] or not r["merged"] or str(r["ahead"]) not in ("0","-"):return messagebox.showwarning("Safe delete","This branch does not meet the safe-delete rules. Force deletion is intentionally unavailable here.",parent=self)
        if messagebox.askyesno("Delete local branch",f"Delete merged local branch {r['branch']} with git branch -d?",parent=self):
            try:messagebox.showinfo("Delete",git(self.repo,"branch","-d",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Delete",str(e),parent=self)

class PullRebaseAdvisor(tk.Toplevel):
    """Compare merge, rebase and fast-forward pull outcomes before changing history."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Pull Strategy Advisor");self.geometry("1100x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Fetch + analyze",self.refresh),("Fast-forward pull",self.ff),("Rebase onto upstream",self.rebase),("Merge upstream",self.merge)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The advisor never chooses a history-changing strategy silently. Rebase creates a timestamped safety branch first.",padding=8).pack(fill="x")
    def state(self):
        b=git(self.repo,"branch","--show-current");u=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");a=git(self.repo,"rev-list","--count",f"{u}..HEAD");d=git(self.repo,"rev-list","--count",f"HEAD..{u}");return b,u,a,d
    def refresh(self):
        try:
            git(self.repo,"fetch","--all","--prune");b,u,a,d=self.state();rec="Already synchronized."
            if d!="0" and a=="0":rec="Fast-forward pull is available and preserves a linear history."
            elif a!="0" and d=="0":rec="Local branch is ahead only. Push after review."
            elif a!="0" and d!="0":rec="Histories diverged. Choose rebase for a linear private branch, or merge when preserving integration topology is preferable."
            v=f"PULL STRATEGY ANALYSIS\n{'='*74}\nBranch: {b}\nUpstream: {u}\nAhead: {a}\nBehind: {d}\nWorking tree: {'Clean' if git(self.repo,'status','--porcelain')=='Completed successfully.' else 'Changed'}\n\nRecommendation: {rec}"
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def ff(self):
        if not self.clean():return messagebox.showwarning("Pull","Commit or stash changes first.",parent=self)
        try:messagebox.showinfo("Pull",git(self.repo,"pull","--ff-only"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Pull",str(e),parent=self)
    def rebase(self):
        import datetime
        if not self.clean():return messagebox.showwarning("Rebase","Commit or stash changes first.",parent=self)
        try:b,u,a,d=self.state();backup=f"gccc-backup/pre-pull-rebase-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}";git(self.repo,"branch",backup)
        except Exception as e:return messagebox.showerror("Rebase",str(e),parent=self)
        if messagebox.askyesno("Rebase",f"Safety branch created: {backup}\n\nRebase {b} onto {u}?",parent=self):
            try:messagebox.showinfo("Rebase",git(self.repo,"rebase",u),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Rebase",str(e),parent=self)
    def merge(self):
        if not self.clean():return messagebox.showwarning("Merge","Commit or stash changes first.",parent=self)
        try:b,u,a,d=self.state()
        except Exception as e:return messagebox.showerror("Merge",str(e),parent=self)
        if messagebox.askyesno("Merge",f"Merge upstream {u} into {b}?",parent=self):
            try:messagebox.showinfo("Merge",git(self.repo,"merge","--no-edit",u),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Merge",str(e),parent=self)
