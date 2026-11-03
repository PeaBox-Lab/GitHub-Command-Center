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

class DetachedHeadRecoveryCenter(tk.Toplevel):
    """Detect detached HEAD and preserve work through a new branch."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Detached HEAD Recovery");self.geometry("1000x660");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Create branch here",command=self.branch).pack(side="left",padx=3);ttk.Button(top,text="Switch to default branch",command=self.default).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        b=git(self.repo,"branch","--show-current");head=git(self.repo,"rev-parse","HEAD");desc=git(self.repo,"show","-s","--date=iso-strict","--pretty=fuller","HEAD");detached=not bool(b)
        v=f"DETACHED HEAD STATUS\n{'='*72}\nDetached: {'Yes' if detached else 'No'}\nCurrent branch: {b or '(none)'}\nHEAD: {head}\n\n{desc}\n\n"+("Create a branch here before switching away if this commit/work should be retained." if detached else "Repository is attached to a normal branch.")
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def branch(self):
        import datetime,re
        name=simpledialog.askstring("Create branch","New branch name:",initialvalue=f"recovered/detached-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",parent=self)
        if name and re.match(r"^[A-Za-z0-9._/-]+$",name):
            try:messagebox.showinfo("Branch",git(self.repo,"switch","-c",name),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Branch",str(e),parent=self)
    def default(self):
        try:
            remote=git(self.repo,"symbolic-ref","refs/remotes/origin/HEAD");branch=remote.replace("refs/remotes/origin/","",1)
        except:branch="main"
        if messagebox.askyesno("Switch branch",f"Switch to {branch}? Uncommitted changes must be compatible.",parent=self):
            try:messagebox.showinfo("Switch",git(self.repo,"switch",branch),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Switch",str(e),parent=self)

class RepositoryStateExportCenter(tk.Toplevel):
    """Export a machine-readable repository-state snapshot for audits and automation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository State Export");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export JSON",command=self.export_json).pack(side="left",padx=3);ttk.Button(top,text="Export Markdown",command=self.export_md).pack(side="left")
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except:return ""
    def refresh(self):
        import json,datetime
        status=self.safe("status","--porcelain=v1").splitlines();branch=self.safe("branch","--show-current");head=self.safe("rev-parse","HEAD");up=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}")
        self.data={"captured":datetime.datetime.now().isoformat(),"repository":Path(self.repo).name,"path":self.repo,"branch":branch,"head":head,"upstream":up,"changes":status,"remotes":self.safe("remote","-v").splitlines(),"tags":self.safe("tag","--sort=-creatordate").splitlines()[:50],"recent_commits":self.safe("log","-25","--date=iso-strict","--pretty=format:%H%x1f%ad%x1f%an%x1f%s").splitlines()}
        self.text.delete("1.0","end");self.text.insert("1.0",json.dumps(self.data,indent=2))
    def export_json(self):
        import json
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile=Path(self.repo).name+"-state.json")
        if p:Path(p).write_text(json.dumps(self.data,indent=2),encoding="utf-8")
    def export_md(self):
        d=self.data;md=f"# Repository state: {d['repository']}\n\n- Captured: {d['captured']}\n- Branch: `{d['branch'] or 'detached'}`\n- HEAD: `{d['head']}`\n- Upstream: `{d['upstream'] or 'none'}`\n\n## Changes\n```text\n"+"\n".join(d["changes"])+"\n```\n\n## Remotes\n```text\n"+"\n".join(d["remotes"])+"\n```\n"
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=Path(self.repo).name+"-state.md")
        if p:Path(p).write_text(md,encoding="utf-8")

class RepositoryRulesCenter(tk.Toplevel):
    """Audit essential repository engineering and governance controls."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Rules Audit");self.geometry("1100x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=4)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        checks=[]
        for f in ("README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md",".gitignore",".gitattributes"):
            checks.append((f,(Path(self.repo)/f).exists()))
        checks.append(("CODEOWNERS",(Path(self.repo)/".github"/"CODEOWNERS").exists()))
        wf=Path(self.repo)/".github"/"workflows";checks.append(("CI workflows",wf.exists() and bool(list(wf.glob("*.y*ml")))))
        try:up=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");checks.append((f"Upstream ({up})",True))
        except:checks.append(("Upstream configured",False))
        self.report="REPOSITORY RULES AUDIT\n"+"="*72+"\n\n"+"\n".join(f"[{'PASS' if ok else 'REVIEW'}] {n}" for n,ok in checks)+f"\n\nOVERALL: {'PASS' if all(x[1] for x in checks) else 'REVIEW REQUIRED'}"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-rules-audit.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class CommitRangeExporter(tk.Toplevel):
    """Export a selected commit range as patches, bundle, or Markdown."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Range Exporter");self.geometry("1050x700");self._build();self.preview()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.base=tk.StringVar(value="HEAD~5");self.tip=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.base,width=22).pack(side="left");ttk.Entry(bar,textvariable=self.tip,width=22).pack(side="left",padx=4)
        for t,c in [("Preview",self.preview),("Patch series",self.patches),("Bundle",self.bundle),("Markdown",self.markdown)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def spec(self):return f"{self.base.get().strip()}..{self.tip.get().strip()}"
    def preview(self):
        try:self.report=git(self.repo,"log","--reverse","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s",self.spec())
        except Exception as e:self.report=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def patches(self):
        d=filedialog.askdirectory(parent=self)
        if d:
            try:messagebox.showinfo("Export",git(self.repo,"format-patch","-o",d,self.spec()),parent=self)
            except Exception as e:messagebox.showerror("Export",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile="commit-range.bundle")
        if p:
            try:messagebox.showinfo("Export",git(self.repo,"bundle","create",p,self.tip.get().strip(),f"^{self.base.get().strip()}"),parent=self)
            except Exception as e:messagebox.showerror("Export",str(e),parent=self)
    def markdown(self):
        self.preview();p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="commit-range.md")
        if p:Path(p).write_text(f"# Commit range {self.spec()}\n\n```text\n{self.report}\n```\n",encoding="utf-8")

class RepositoryOnboardingCenter(tk.Toplevel):
    """Turn an existing folder/repository into a collaboration-ready project."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Onboarding Center");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Create missing basics",self.create_basics),("Initialize Git",self.init_git),("Open Rules Audit",lambda:RepositoryRulesCenter(self,self.repo))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        root=Path(self.repo);checks=[]
        for name in (".git","README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md",".gitignore",".gitattributes"):
            checks.append((name,(root/name).exists()))
        self.report="REPOSITORY ONBOARDING\n"+"="*72+"\n\n"+"\n".join(f"[{'PASS' if ok else 'MISSING'}] {name}" for name,ok in checks)
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def init_git(self):
        if (Path(self.repo)/".git").exists():return messagebox.showinfo("Onboarding","Git is already initialized.",parent=self)
        try:messagebox.showinfo("Onboarding",git(self.repo,"init"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Onboarding",str(e),parent=self)
    def write_if_missing(self,name,text):
        p=Path(self.repo)/name
        if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8");return True
        return False
    def create_basics(self):
        created=[]
        templates={
          "README.md":f"# {Path(self.repo).name}\n\nProject description.\n",
          "CHANGELOG.md":"# Changelog\n\n## Unreleased\n\n",
          "SECURITY.md":"# Security Policy\n\nReport vulnerabilities privately to the maintainers.\n",
          "CONTRIBUTING.md":"# Contributing\n\nUse focused branches, tests, documentation, and pull requests.\n",
          ".gitignore":"__pycache__/\n*.py[cod]\n.venv/\n.env\nbuild/\ndist/\n",
          ".gitattributes":"* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.zip binary\n"
        }
        for n,v in templates.items():
            if self.write_if_missing(n,v):created.append(n)
        messagebox.showinfo("Onboarding","Created:\n"+("\n".join(created) if created else "No missing starter files."),parent=self);self.refresh()

class RepositoryAuditPackCenter(tk.Toplevel):
    """Generate a compact technical audit pack from local Git evidence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Audit Pack");self.geometry("1100x740");self._build();self.generate()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Regenerate",command=self.generate).pack(side="left");ttk.Button(bar,text="Export Markdown",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return f"Unavailable: {e}"
    def generate(self):
        status=self.safe("status","--short","--branch");remotes=self.safe("remote","-v");fsck=self.safe("fsck","--no-progress");recent=self.safe("log","-20","--date=short","--pretty=format:- %h %ad %an: %s");tags=self.safe("tag","--sort=-creatordate");config=self.safe("config","--list","--show-origin")
        self.report=f"# Repository Audit Pack: {Path(self.repo).name}\n\n## Status\n```text\n{status}\n```\n\n## Remotes\n```text\n{remotes}\n```\n\n## Recent commits\n{recent}\n\n## Tags\n```text\n{tags}\n```\n\n## Integrity\n```text\n{fsck}\n```\n\n## Git configuration origins\n```text\n{config}\n```\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=f"{Path(self.repo).name}-audit-pack.md")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class BackupBranchManager(tk.Toplevel):
    """Inventory and clean old gccc-backup branches conservatively."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safety Branch Manager");self.geometry("1100x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Inspect",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Delete selected",command=self.delete).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("branch","date","hash","subject"),show="headings")
        for c,t,w in [("branch","Safety branch",390),("date","Date",130),("hash","Commit",100),("subject","Subject",430)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Only gccc-backup/* branches are shown. Delete uses normal git branch -d and will refuse unmerged safety branches.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"for-each-ref","--sort=-committerdate","--format=%(refname:short)%09%(committerdate:short)%09%(objectname:short)%09%(subject)","refs/heads/gccc-backup/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3)
            if len(p)==4:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=p)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--oneline",r[0])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete(self):
        r=self.selected()
        if r and messagebox.askyesno("Safety branch",f"Delete merged safety branch {r[0]}?",parent=self):
            try:messagebox.showinfo("Safety branch",git(self.repo,"branch","-d",r[0]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Safety branch",str(e),parent=self)

class UpstreamHealthCenter(tk.Toplevel):
    """Audit local branches for upstream health, remote existence, and divergence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Upstream Health Center");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Fetch + refresh",self.refresh),("Set upstream",self.set_upstream),("Unset upstream",self.unset_upstream),("Publish branch",self.publish)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("branch","upstream","remote_exists","ahead","behind","status"),show="headings")
        for c,t,w in [("branch","Local branch",260),("upstream","Upstream",270),("remote_exists","Remote exists",110),("ahead","Ahead",70),("behind","Behind",70),("status","Assessment",300)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Use this center after branch renames, remote cleanup, or repository migrations to find broken upstream relationships.",padding=8).pack(fill="x")
    def refresh(self):
        try:git(self.repo,"fetch","--all","--prune")
        except:pass
        raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(upstream:short)","refs/heads/");remote_refs=set()
        try:remote_refs=set(x for x in git(self.repo,"for-each-ref","--format=%(refname:short)","refs/remotes/").splitlines())
        except:pass
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",1);branch=p[0];up=p[1] if len(p)>1 else "";exists=bool(up and up in remote_refs);a=b="-";status="No upstream"
            if up and exists:
                try:a=git(self.repo,"rev-list","--count",f"{up}..{branch}");b=git(self.repo,"rev-list","--count",f"{branch}..{up}")
                except:pass
                status="Synchronized" if a=="0" and b=="0" else "Ahead" if a!="0" and b=="0" else "Behind" if a=="0" and b!="0" else "Diverged"
            elif up:status="Broken upstream"
            r=dict(branch=branch,up=up,exists=exists,a=a,b=b,status=status);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(branch,up or "-","Yes" if exists else "No",a,b,status))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def set_upstream(self):
        r=self.selected()
        if not r:return
        value=simpledialog.askstring("Set upstream",f"Upstream for {r['branch']} (example origin/{r['branch']}):",parent=self)
        if value:
            try:messagebox.showinfo("Upstream",git(self.repo,"branch","--set-upstream-to",value,r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Upstream",str(e),parent=self)
    def unset_upstream(self):
        r=self.selected()
        if r and r["up"] and messagebox.askyesno("Unset upstream",f"Remove upstream configuration from {r['branch']}?",parent=self):
            try:messagebox.showinfo("Upstream",git(self.repo,"branch","--unset-upstream",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Upstream",str(e),parent=self)
    def publish(self):
        r=self.selected()
        if r and messagebox.askyesno("Publish branch",f"Push {r['branch']} to origin and set upstream?",parent=self):
            try:messagebox.showinfo("Publish",git(self.repo,"push","-u","origin",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Publish",str(e),parent=self)
