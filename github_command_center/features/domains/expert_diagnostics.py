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

class FileEvolutionCenter(tk.Toplevel):
    """Trace a file across renames with per-commit stats and historical content."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("File Evolution Center");self.geometry("1250x780");self.rows=[];self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.path=tk.StringVar();ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Load evolution",command=self.load).pack(side="left",padx=3);ttk.Button(bar,text="Export selected version",command=self.export).pack(side="left")
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.list=tk.Listbox(a,font=("Consolas",9));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.show())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def load(self):
        p=self.path.get().strip()
        if not p:return
        try:raw=git(self.repo,"log","--follow","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%s","--",p)
        except Exception as e:return messagebox.showerror("File evolution",str(e),parent=self)
        self.rows=[];self.list.delete(0,"end")
        for line in raw.splitlines():
            q=line.split("\x1f",4)
            if len(q)==5:self.rows.append(q);self.list.insert("end",f"{q[1]}  {q[2]}  {q[4]}")
    def selected(self):
        s=self.list.curselection();return self.rows[s[0]] if s else None
    def show(self):
        r=self.selected();p=self.path.get().strip()
        if not r:return
        try:
            stat=git(self.repo,"show","--stat","--find-renames",r[0],"--",p);content=run_process(["git","show",f"{r[0]}:{p}"],cwd=self.repo,timeout=120,binary=True)
            body=content.stdout.decode("utf-8") if content.returncode==0 and b"\x00" not in content.stdout[:8192] else "(Historical path unavailable at this commit, renamed, deleted, or binary.)"
            v=stat+"\n\nHISTORICAL CONTENT\n"+"="*72+"\n"+body
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        r=self.selected();p=self.path.get().strip()
        if not r:return
        dest=filedialog.asksaveasfilename(parent=self,initialfile=Path(p).name)
        if dest:
            out=run_process(["git","show",f"{r[0]}:{p}"],cwd=self.repo,timeout=120,binary=True)
            if out.returncode:messagebox.showerror("Export",out.stderr.decode("utf-8"),parent=self)
            else:Path(dest).write_bytes(out.stdout);messagebox.showinfo("Export",f"Saved {dest}",parent=self)

class GitRemoteShowCenter(tk.Toplevel):
    """Detailed remote tracking and stale-branch report using git remote show."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote Details Center");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.remote=tk.StringVar(value="origin");self.box=ttk.Combobox(bar,textvariable=self.remote,width=22);self.box.pack(side="left");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left",padx=3);ttk.Button(bar,text="Query remote",command=self.query).pack(side="left");ttk.Button(bar,text="Query cached only",command=self.cached).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        rem=[x for x in git(self.repo,"remote").splitlines() if x and x!="Completed successfully."];self.box["values"]=rem
        if rem and self.remote.get() not in rem:self.remote.set(rem[0])
        self.cached()
    def show(self,args):
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def query(self):self.show(["remote","show",self.remote.get().strip()])
    def cached(self):self.show(["remote","show","-n",self.remote.get().strip()])

class ProtocolDiagnosticsCenter(tk.Toplevel):
    """Inspect Git wire-protocol capabilities and remote advertisement without mutation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Protocol Diagnostics");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.remote=tk.StringVar(value="origin");self.box=ttk.Combobox(bar,textvariable=self.remote,width=22);self.box.pack(side="left")
        for text,cmd in [("Refresh",self.refresh),("List remote refs",self.refs),("Protocol v2 trace",self.trace),("Cached remote details",self.cached)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Read-only diagnostics. Protocol tracing can expose repository/ref names but this center redacts obvious credential-bearing URL userinfo before display.",padding=8).pack(fill="x")
    def remotes(self):return [x for x in git(self.repo,"remote").splitlines() if x and x!="Completed successfully."]
    def redact(self,text):
        import re
        return re.sub(r"(https?://)[^/@\s]+@",r"\1***@",text)
    def refresh(self):
        rem=self.remotes();self.box["values"]=rem
        if rem and self.remote.get() not in rem:self.remote.set(rem[0])
        try:
            version=git(self.repo,"--version");proto=git(self.repo,"config","--get","protocol.version")
        except Exception as e:proto=str(e);version=""
        self.show(f"GIT PROTOCOL DIAGNOSTICS\n{'='*72}\n{version}\nConfigured protocol.version: {proto}\nRemote: {self.remote.get()}")
    def show(self,v):self.out.delete("1.0","end");self.out.insert("1.0",self.redact(v))
    def refs(self):
        try:self.show(git(self.repo,"ls-remote","--symref",self.remote.get().strip()))
        except Exception as e:self.show(str(e))
    def cached(self):
        try:self.show(git(self.repo,"remote","show","-n",self.remote.get().strip()))
        except Exception as e:self.show(str(e))
    def trace(self):
        import os
        env=os.environ.copy();env["GIT_TRACE_PACKET"]="1";env["GIT_TRACE"]="1";env["GIT_PROTOCOL"]="version=2"
        try:
            r=run_process(["git","ls-remote",self.remote.get().strip()],cwd=self.repo,env=env,timeout=120);self.show((r.stdout+"\n"+r.stderr).strip())
        except Exception as e:self.show(str(e))

class AlternatesInspectorCenter(tk.Toplevel):
    """Inspect object alternates, shared clones, and linked-object storage."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Object Alternates Inspector");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Export report",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Dissociate by repack",command=self.dissociate).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Dissociate copies reachable objects into this repository using repack -a -d. It can require substantial disk space and requires confirmation.",padding=8).pack(fill="x")
    def gitdir(self):
        p=Path(git(self.repo,"rev-parse","--git-dir"));return (Path(self.repo)/p).resolve() if not p.is_absolute() else p
    def refresh(self):
        gd=self.gitdir();alt=gd/"objects"/"info"/"alternates";alternates=alt.read_text(encoding="utf-8") if alt.exists() else "None"
        env=os.environ.get("GIT_ALTERNATE_OBJECT_DIRECTORIES","Not set");objects=git(self.repo,"count-objects","-vH");self.report=f"OBJECT ALTERNATES\n{'='*72}\nGit dir: {gd}\nAlternates file: {alt}\n\nConfigured alternates:\n{alternates}\n\nEnvironment alternates:\n{env}\n\nLOCAL OBJECT STATUS\n{objects}"
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="object-alternates.txt")
        if p:Path(p).write_text(self.report)
    def dissociate(self):
        if not messagebox.askyesno("Dissociate objects","Copy all reachable objects into this repository with `git repack -a -d`? This may consume significant disk space.",parent=self):return
        try:messagebox.showinfo("Dissociate",git(self.repo,"repack","-a","-d"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Dissociate",str(e),parent=self)

class EolNormalizationCenter(tk.Toplevel):
    """Audit line-ending behavior and preview repository normalization."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("EOL Normalization Center");self.geometry("1120x730");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.path=tk.StringVar(value=".");ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True)
        for text,cmd in [("Refresh",self.refresh),("Check attributes",self.attributes),("Preview renormalize",self.preview),("Stage renormalization",self.renormalize)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Renormalization can stage many files. Review `.gitattributes`, use Preview, and commit normalization separately from functional changes.",padding=8).pack(fill="x")
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        v=f"EOL CONFIGURATION\n{'='*72}\ncore.autocrlf: {self.safe('config','--get','core.autocrlf')}\ncore.eol: {self.safe('config','--get','core.eol')}\ncore.safecrlf: {self.safe('config','--get','core.safecrlf')}\n\nATTRIBUTES FILE\n"
        p=Path(self.repo)/".gitattributes";v+=p.read_text(encoding="utf-8") if p.exists() else "Missing .gitattributes"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def attributes(self):
        p=self.path.get().strip() or "."
        try:v=git(self.repo,"check-attr","text","eol","working-tree-encoding","--",p)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def preview(self):
        p=self.path.get().strip() or "."
        try:v=git(self.repo,"add","--renormalize","--dry-run","--",p)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","RENORMALIZE PREVIEW\n"+"="*72+"\n"+v)
    def renormalize(self):
        p=self.path.get().strip() or "."
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Renormalize","Start from a clean working tree so normalization remains isolated.",parent=self)
        if messagebox.askyesno("Renormalize",f"Stage line-ending normalization for pathspec `{p}`? Review the staged diff before committing.",parent=self):
            try:messagebox.showinfo("Renormalize",git(self.repo,"add","--renormalize","--",p),parent=self)
            except Exception as e:messagebox.showerror("Renormalize",str(e),parent=self)

class CommitMessageAuditCenter(tk.Toplevel):
    """Audit commit-message quality and Conventional Commit coverage over a selected range."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Message Audit");self.geometry("1160x740");self._build();self.audit()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.range=tk.StringVar(value="HEAD~100..HEAD");self.minlen=tk.IntVar(value=12)
        ttk.Entry(bar,textvariable=self.range).pack(side="left",fill="x",expand=True);ttk.Label(bar,text="Min subject length").pack(side="left",padx=(8,2));ttk.Spinbox(bar,from_=5,to=100,textvariable=self.minlen,width=6).pack(side="left")
        ttk.Button(bar,text="Audit",command=self.audit).pack(side="left",padx=4);ttk.Button(bar,text="Export",command=self.export).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("hash","date","author","status","subject"),show="headings")
        for c,t,w in [("hash","Commit",90),("date","Date",110),("author","Author",170),("status","Assessment",180),("subject","Subject",560)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.summary=tk.Text(self,height=12,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def audit(self):
        import re
        spec=self.range.get().strip() or "HEAD~100..HEAD"
        try:raw=git(self.repo,"log","--date=short","--pretty=format:%h%x1f%ad%x1f%an%x1f%s",spec)
        except Exception as e:raw="";self.report=str(e)
        conv=re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?!?: .+")
        self.tree.delete(*self.tree.get_children());rows=[];good=short=generic=merge=0
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)!=4:continue
            subject=p[3];issues=[]
            if subject.startswith("Merge "):merge+=1;issues.append("Merge commit")
            elif conv.match(subject):good+=1
            else:issues.append("Non-conventional")
            if len(subject)<int(self.minlen.get()):short+=1;issues.append("Too short")
            if subject.lower() in ("update","changes","fix","wip","misc","work"):generic+=1;issues.append("Generic")
            status="PASS" if not issues else ", ".join(issues);rows.append((*p,status));self.tree.insert("","end",values=(p[0],p[1],p[2],status,subject))
        total=len(rows);coverage=(good/total*100) if total else 0
        self.report=f"COMMIT MESSAGE AUDIT\n{'='*72}\nRange: {spec}\nCommits: {total}\nConventional subjects: {good} ({coverage:.1f}%)\nShort subjects: {short}\nGeneric subjects: {generic}\nMerge commits: {merge}\n\nRecommended format:\n  feat(scope): concise imperative summary\n\nKeep the subject specific, use a body for rationale/validation, and reference issues in the footer."
        self.summary.delete("1.0","end");self.summary.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="commit-message-audit.txt")
        if p:Path(p).write_text(self.report)

class GitArchiveManifestCenter(tk.Toplevel):
    """Create and verify a tracked-file manifest for a selected revision."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Revision Manifest Center");self.geometry("1080x700");self.ref=tk.StringVar(value="HEAD");self._build();self.generate()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Entry(bar,textvariable=self.ref).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Generate",command=self.generate).pack(side="left",padx=3);ttk.Button(bar,text="Export manifest",command=self.export).pack(side="left");ttk.Button(bar,text="Verify manifest",command=self.verify).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The manifest records Git blob IDs and paths for a revision. Verification compares the manifest to the selected revision without checking it out.",padding=8).pack(fill="x")
    def generate(self):
        ref=self.ref.get().strip() or "HEAD"
        try:
            resolved=git(self.repo,"rev-parse",f"{ref}^{{commit}}");raw=git(self.repo,"ls-tree","-r","--full-tree",ref);lines=[f"# revision {ref}",f"# commit {resolved}"]
            for line in raw.splitlines():
                if "\t" not in line:continue
                meta,path=line.split("\t",1);p=meta.split()
                if len(p)>=3:lines.append(f"{p[0]} {p[1]} {p[2]}  {path}")
            self.manifest="\n".join(lines)+"\n"
        except Exception as e:self.manifest=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.manifest)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="revision-manifest.txt")
        if p:Path(p).write_text(self.manifest)
    def verify(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Manifest","*.txt"),("All files","*")])
        if not p:return
        expected={}
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "  " not in line:continue
            meta,path=line.split("  ",1);parts=meta.split()
            if len(parts)>=3:expected[path]=parts[2]
        ref=self.ref.get().strip() or "HEAD";actual={}
        try:
            raw=git(self.repo,"ls-tree","-r","--full-tree",ref)
            for line in raw.splitlines():
                if "\t" in line:
                    meta,path=line.split("\t",1);parts=meta.split()
                    if len(parts)>=3:actual[path]=parts[2]
            added=sorted(set(actual)-set(expected));missing=sorted(set(expected)-set(actual));changed=sorted(p for p in set(actual)&set(expected) if actual[p]!=expected[p]);v=f"MANIFEST VERIFICATION\n{'='*72}\nRevision: {ref}\nExpected paths: {len(expected)}\nActual paths: {len(actual)}\nAdded: {len(added)}\nMissing: {len(missing)}\nChanged blobs: {len(changed)}\n\nADDED\n"+"\n".join(added)+"\n\nMISSING\n"+"\n".join(missing)+"\n\nCHANGED\n"+"\n".join(changed)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class BranchDescriptionCenter(tk.Toplevel):
    """Manage local branch descriptions stored in Git config."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Branch Description Center");self.geometry("1080x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Load selected",command=self.load).pack(side="left",padx=3);ttk.Button(bar,text="Save description",command=self.save).pack(side="left");ttk.Button(bar,text="Clear description",command=self.clear).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.tree=ttk.Treeview(a,columns=("branch","description"),show="headings");self.tree.heading("branch",text="Branch");self.tree.heading("description",text="Description");self.tree.column("branch",width=280);self.tree.column("description",width=410);self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.load())
        self.editor=tk.Text(b,wrap="word",undo=True,font=("Segoe UI",10));self.editor.pack(fill="both",expand=True)
        ttk.Label(self,text="Branch descriptions are local Git config metadata. They are not pushed with the branch unless separately documented.",padding=8).pack(fill="x")
    def refresh(self):
        branches=[x for x in git(self.repo,"for-each-ref","--format=%(refname:short)","refs/heads/").splitlines() if x];self.rows=[];self.tree.delete(*self.tree.get_children())
        for b in branches:
            try:d=git(self.repo,"config","--get",f"branch.{b}.description")
            except:d=""
            if d=="Completed successfully.":d=""
            self.rows.append((b,d));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(b,d.replace("\n"," ")[:200]))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def load(self):
        r=self.selected();self.editor.delete("1.0","end")
        if r:self.editor.insert("1.0",r[1])
    def save(self):
        r=self.selected()
        if not r:return
        d=self.editor.get("1.0","end-1c").strip()
        try:git(self.repo,"config",f"branch.{r[0]}.description",d);messagebox.showinfo("Branch description","Saved locally.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Branch description",str(e),parent=self)
    def clear(self):
        r=self.selected()
        if r and messagebox.askyesno("Branch description",f"Clear description for {r[0]}?",parent=self):
            try:git(self.repo,"config","--unset",f"branch.{r[0]}.description");self.refresh();self.editor.delete("1.0","end")
            except Exception as e:messagebox.showerror("Branch description",str(e),parent=self)

class SelectiveStashCenter(tk.Toplevel):
    """Create a stash from selected tracked paths using Git pathspecs."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Selective Stash Center");self.geometry("1120x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.message=tk.StringVar(value="Selective stash");self.keep_index=tk.BooleanVar();self.include_untracked=tk.BooleanVar()
        ttk.Entry(bar,textvariable=self.message).pack(side="left",fill="x",expand=True);ttk.Checkbutton(bar,text="Keep index",variable=self.keep_index).pack(side="left",padx=4);ttk.Checkbutton(bar,text="Include untracked",variable=self.include_untracked).pack(side="left");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left",padx=4);ttk.Button(bar,text="Stash selected",command=self.stash,style="Accent.TButton").pack(side="left")
        self.tree=ttk.Treeview(self,columns=("state","path"),show="headings",selectmode="extended");self.tree.heading("state",text="State");self.tree.heading("path",text="Changed path");self.tree.column("state",width=90);self.tree.column("path",width=920);self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Only selected paths are sent to `git stash push -- <paths>`. Review staged changes carefully when using Keep index.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"status","--porcelain=v1");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if len(line)>3:
                path=line[3:]
                if " -> " in path:path=path.split(" -> ",1)[1]
                row=(line[:2],path);self.rows.append(row);self.tree.insert("","end",iid=str(len(self.rows)-1),values=row)
        self.out.delete("1.0","end");self.out.insert("1.0",f"Changed paths: {len(self.rows)}\nSelect one or more paths to create a focused stash.")
    def selected(self):return [self.rows[int(i)][1] for i in self.tree.selection()]
    def stash(self):
        paths=self.selected()
        if not paths:return messagebox.showwarning("Selective stash","Select at least one changed path.",parent=self)
        args=["stash","push","-m",self.message.get().strip() or "Selective stash"]
        if self.keep_index.get():args.append("--keep-index")
        if self.include_untracked.get():args.append("--include-untracked")
        args += ["--",*paths]
        if not messagebox.askyesno("Selective stash",f"Stash {len(paths)} selected path(s)?",parent=self):return
        try:v=git(self.repo,*args);messagebox.showinfo("Selective stash",v,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Selective stash",str(e),parent=self)

class WorktreeMoveCenter(tk.Toplevel):
    """Move a linked worktree to a new folder and repair its metadata."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Worktree Move Center");self.geometry("1120x710");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.destination=tk.StringVar();ttk.Entry(bar,textvariable=self.destination).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Browse destination",command=self.browse).pack(side="left",padx=3);ttk.Button(bar,text="Move selected",command=self.move).pack(side="left");ttk.Button(bar,text="Repair all",command=self.repair).pack(side="left",padx=3);ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("path","branch","head","locked"),show="headings")
        for c,t,w in [("path","Worktree",560),("branch","Branch",260),("head","HEAD",120),("locked","Locked",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The primary worktree cannot normally be moved with `git worktree move`. Commit or stash changes in the selected worktree before moving it.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"worktree","list","--porcelain");self.rows=[];cur={}
        for line in raw.splitlines()+[""]:
            if not line:
                if cur:self.rows.append(cur);cur={}
            elif " " in line:
                k,v=line.split(" ",1);cur[k]=v
            else:cur[line]="true"
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r.get("worktree",""),r.get("branch","").replace("refs/heads/",""),r.get("HEAD","")[:12],"Yes" if "locked" in r else "No"))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.destination.set(p)
    def move(self):
        r=self.selected();dest=self.destination.get().strip()
        if not r or not dest:return
        src=r.get("worktree","")
        if Path(src).resolve()==Path(self.repo).resolve():return messagebox.showwarning("Worktree move","The primary worktree is not moved by this workflow.",parent=self)
        try:
            state=git(src,"status","--porcelain")
            if state!="Completed successfully.":return messagebox.showwarning("Worktree move","Commit or stash changes in the selected worktree first.",parent=self)
        except Exception as e:return messagebox.showerror("Worktree move",str(e),parent=self)
        if messagebox.askyesno("Move worktree",f"Move worktree from:\n{src}\n\nto:\n{dest}?",parent=self):
            try:messagebox.showinfo("Worktree move",git(self.repo,"worktree","move",src,dest),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Worktree move",str(e),parent=self)
    def repair(self):
        try:messagebox.showinfo("Worktree repair",git(self.repo,"worktree","repair"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree repair",str(e),parent=self)
