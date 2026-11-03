"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.process_gateway import run_process, start_process
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

class MailmapCenter(tk.Toplevel):
    """Audit contributor identities and maintain a repository .mailmap file."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.mailmap=Path(repo)/".mailmap";self.title("Contributor Mailmap Center");self.geometry("1120x740");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh identities",self.refresh),("Load .mailmap",self.load),("Save .mailmap",self.save),("Preview canonical shortlog",self.preview)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        ttk.Label(a,text="Raw contributor identities",font=("Segoe UI Semibold",10)).pack(anchor="w");self.ids=tk.Text(a,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.ids.pack(fill="both",expand=True)
        ttk.Label(b,text=".mailmap editor",font=("Segoe UI Semibold",10)).pack(anchor="w");self.editor=tk.Text(b,wrap="none",undo=True,font=("Consolas",9));self.editor.pack(fill="both",expand=True)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#111827",fg="#dbeafe");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text=".mailmap consolidates alternate author names/emails for shortlog and reporting without rewriting commits.",padding=8).pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"log","--all","--format=%aN <%aE>")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        unique=sorted(set(v.splitlines()),key=str.lower);self.ids.delete("1.0","end");self.ids.insert("1.0","\n".join(unique));self.load()
    def load(self):
        self.editor.delete("1.0","end");self.editor.insert("1.0",self.mailmap.read_text(encoding="utf-8",errors="replace") if self.mailmap.exists() else "# Canonical Name <canonical@email> <alternate@email>\n")
    def save(self):
        self.mailmap.write_text(self.editor.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Mailmap","Saved .mailmap. Review and commit it for shared canonical reporting.",parent=self);self.preview()
    def preview(self):
        try:v=git(self.repo,"shortlog","-sne","--all","--use-mailmap")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class PatchIdCenter(tk.Toplevel):
    """Compare patch identity to detect equivalent changes across commits."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Patch Identity Comparator");self.geometry("1050x680");self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.a=tk.StringVar(value="HEAD~1");self.b=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.a,width=26).pack(side="left");ttk.Entry(bar,textvariable=self.b,width=26).pack(side="left",padx=4);ttk.Button(bar,text="Compare patch IDs",command=self.compare).pack(side="left");ttk.Button(bar,text="Range equivalent check",command=self.range_check).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Patch IDs compare the introduced change while ignoring commit metadata. Equivalent patch IDs can reveal duplicate cherry-picks or rebased equivalents.",padding=8).pack(fill="x")
    def patch_id(self,ref):
        show=run_process(["git","show","--pretty=format:",ref],cwd=self.repo,capture_output=True,timeout=120)
        if show.returncode:raise GitError(show.stderr.decode("utf-8",errors="replace"))
        pid=run_process(["git","patch-id","--stable"],cwd=self.repo,input=show.stdout,capture_output=True,timeout=120)
        if pid.returncode:raise GitError(pid.stderr.decode("utf-8",errors="replace"))
        return pid.stdout.decode("utf-8",errors="replace").split()[0]
    def compare(self):
        try:
            pa=self.patch_id(self.a.get().strip());pb=self.patch_id(self.b.get().strip());v=f"PATCH ID COMPARISON\n{'='*72}\n{self.a.get()}: {pa}\n{self.b.get()}: {pb}\n\nResult: {'EQUIVALENT CHANGES' if pa==pb else 'DIFFERENT CHANGES'}"
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def range_check(self):
        a=self.a.get().strip();b=self.b.get().strip()
        try:v=git(self.repo,"cherry","-v",a,b)
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",f"git cherry -v {a} {b}\n{'='*72}\n{v}\n\n'-' indicates an equivalent patch already exists upstream; '+' indicates a unique patch.")

class CredentialRedactionAuditCenter(tk.Toplevel):
    """Audit tracked text for likely credential patterns without printing full secret values."""
    PATTERNS=[
        ("GitHub token", r"gh[pousr]_[A-Za-z0-9_]{20,}"),
        ("AWS access key", r"AKIA[0-9A-Z]{16}"),
        ("Private key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        ("Generic secret assignment", r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s]{8,}"),
    ]
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Credential Redaction Audit");self.geometry("1120x730");self._build();self.scan()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Scan tracked text",command=self.scan).pack(side="left");ttk.Button(bar,text="Export redacted report",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Open Security Center",command=lambda:SecurityCenter(self,self.repo)).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("kind","file","line","preview"),show="headings")
        for c,t,w in [("kind","Finding",180),("file","File",360),("line","Line",70),("preview","Redacted preview",470)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The audit redacts matches in the UI/report. A finding is a review signal, not proof that a valid secret exists. Rotate real exposed credentials instead of merely deleting them from the latest commit.",padding=8).pack(fill="x")
    def scan(self):
        import re
        files=git(self.repo,"ls-files").splitlines();self.findings=[];self.tree.delete(*self.tree.get_children())
        for rel in files:
            p=Path(self.repo)/rel
            try:
                if not p.is_file() or p.stat().st_size>2*1024*1024:continue
                data=p.read_text(encoding="utf-8",errors="strict")
            except HANDLED_EXCEPTIONS:continue
            for n,line in enumerate(data.splitlines(),1):
                for label,pattern in self.PATTERNS:
                    if re.search(pattern,line):
                        red=re.sub(pattern,"***REDACTED***",line)[:300];self.findings.append((label,rel,n,red));self.tree.insert("","end",values=(label,rel,n,red))
        self.report="CREDENTIAL REDACTION AUDIT\n"+"="*72+f"\nFindings: {len(self.findings)}\n\n"+"\n".join(f"{k} | {f}:{n} | {p}" for k,f,n,p in self.findings)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="credential-redaction-audit.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class RefConsistencyCenter(tk.Toplevel):
    """Validate local refs and detect broken symbolic refs or missing upstream targets."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Ref Consistency Center");self.geometry("1100x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Fetch + prune",command=self.fetch).pack(side="left",padx=3);ttk.Button(bar,text="Open Ref Browser",command=lambda:UnifiedRefBrowser(self,self.repo)).pack(side="left")
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except HANDLED_EXCEPTIONS as e:return "ERROR: "+str(e)
    def refresh(self):
        refs=self.safe("show-ref","--head","--dereference");head=self.safe("symbolic-ref","-q","HEAD");origin_head=self.safe("symbolic-ref","-q","refs/remotes/origin/HEAD");verify=self.safe("fsck","--connectivity-only","--no-dangling");report=f"REF CONSISTENCY\n{'='*72}\nHEAD symbolic ref: {head}\nOrigin default ref: {origin_head}\n\nCONNECTIVITY\n{verify}\n\nREFS\n{refs}"
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def fetch(self):
        try:messagebox.showinfo("Refs",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Refs",str(e),parent=self)

class ReleaseBranchPlanner(tk.Toplevel):
    """Create a release branch from a deliberate base after validating cleanliness and ref existence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Branch Planner");self.geometry("980x650");self._build();self.preview()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.base=tk.StringVar(value="main");self.name=tk.StringVar(value="release/")
        ttk.Label(f,text="Base ref").grid(row=0,column=0,sticky="w",pady=6);ttk.Entry(f,textvariable=self.base).grid(row=0,column=1,sticky="ew",padx=8)
        ttk.Label(f,text="New release branch").grid(row=1,column=0,sticky="w",pady=6);ttk.Entry(f,textvariable=self.name).grid(row=1,column=1,sticky="ew",padx=8);f.columnconfigure(1,weight=1)
        ttk.Button(f,text="Preview base",command=self.preview).grid(row=2,column=0,pady=8);ttk.Button(f,text="Create + switch",command=self.create,style="Accent.TButton").grid(row=2,column=1,sticky="e",pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=3,column=0,columnspan=2,sticky="nsew");f.rowconfigure(3,weight=1)
    def preview(self):
        b=self.base.get().strip()
        try:v=git(self.repo,"show","-s","--date=iso-strict","--pretty=fuller",b)+"\n\n"+git(self.repo,"log","-10","--oneline",b)
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def create(self):
        import re
        b=self.base.get().strip();n=self.name.get().strip()
        if not n or not re.match(r"^[A-Za-z0-9._/-]+$",n):return messagebox.showwarning("Release branch","Enter a valid branch name.",parent=self)
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Release branch","Commit or stash local changes first.",parent=self)
        try:git(self.repo,"rev-parse","--verify",b)
        except HANDLED_EXCEPTIONS as e:return messagebox.showerror("Release branch",str(e),parent=self)
        if messagebox.askyesno("Release branch",f"Create and switch to {n} from {b}?",parent=self):
            try:messagebox.showinfo("Release branch",git(self.repo,"switch","-c",n,b),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Release branch",str(e),parent=self)

class GitSwitchRestoreCenter(tk.Toplevel):
    """Guided modern switch/restore workflows with explicit source and path selection."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Switch & Restore Center");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.branch=tk.StringVar();self.source=tk.StringVar(value="HEAD");self.path=tk.StringVar()
        ttk.Entry(top,textvariable=self.branch,width=24).pack(side="left");ttk.Button(top,text="Switch branch",command=self.switch).pack(side="left",padx=3);ttk.Button(top,text="Create + switch",command=self.create).pack(side="left")
        row=ttk.Frame(self,padding=(8,0));row.pack(fill="x");ttk.Entry(row,textvariable=self.source,width=24).pack(side="left");ttk.Entry(row,textvariable=self.path).pack(side="left",fill="x",expand=True,padx=4);ttk.Button(row,text="Restore working file",command=lambda:self.restore(False)).pack(side="left");ttk.Button(row,text="Restore staged + working",command=lambda:self.restore(True)).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Restore can discard file changes. A preview of the selected path is shown before execution and confirmation is required.",padding=8).pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"branch","-vv")+"\n\nSTATUS\n"+git(self.repo,"status","--short","--branch")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def switch(self):
        b=self.branch.get().strip()
        if b:
            try:messagebox.showinfo("Switch",git(self.repo,"switch",b),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Switch",str(e),parent=self)
    def create(self):
        b=self.branch.get().strip()
        if b:
            try:messagebox.showinfo("Switch",git(self.repo,"switch","-c",b),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Switch",str(e),parent=self)
    def restore(self,staged):
        p=self.path.get().strip();src=self.source.get().strip() or "HEAD"
        if not p:return
        try:preview=git(self.repo,"diff","--",p)
        except HANDLED_EXCEPTIONS as e:preview=str(e)
        if not messagebox.askyesno("Restore path",f"Restore {p} from {src}?\n\nCurrent diff preview:\n{preview[:1600]}",parent=self):return
        args=["restore",f"--source={src}"]+(["--staged","--worktree"] if staged else ["--worktree"])+["--",p]
        try:messagebox.showinfo("Restore",git(self.repo,*args),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Restore",str(e),parent=self)

class RebaseStateCenter(tk.Toplevel):
    """Inspect an in-progress rebase state without guessing what Git is doing."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Rebase State Inspector");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Continue",lambda:self.cmd("--continue")),("Skip",lambda:self.cmd("--skip")),("Abort",lambda:self.cmd("--abort")),("Edit todo",self.todo)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def gitdir(self):
        p=git(self.repo,"rev-parse","--git-dir");return (Path(self.repo)/p).resolve() if not Path(p).is_absolute() else Path(p)
    def refresh(self):
        gd=self.gitdir();merge=gd/"rebase-merge";apply=gd/"rebase-apply";state=merge if merge.exists() else apply if apply.exists() else None
        if not state:v="No rebase session is currently active."
        else:
            files=[]
            for n in ("head-name","onto","orig-head","done","git-rebase-todo","message","stopped-sha"):
                p=state/n
                if p.exists():files.append(f"## {n}\n{p.read_text(encoding='utf-8',errors='replace')[:8000]}")
            try:conf=git(self.repo,"diff","--name-only","--diff-filter=U")
            except HANDLED_EXCEPTIONS:conf=""
            v=f"ACTIVE REBASE: {state}\n{'='*72}\n\n"+"\n\n".join(files)+f"\n\nUNRESOLVED FILES\n{conf}"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def cmd(self,a):
        try:messagebox.showinfo("Rebase",git(self.repo,"rebase",a),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Rebase",str(e),parent=self)
    def todo(self):
        gd=self.gitdir();p=gd/"rebase-merge"/"git-rebase-todo"
        if not p.exists():return messagebox.showinfo("Rebase","No editable interactive-rebase todo file found.",parent=self)
        w=tk.Toplevel(self);w.title("Rebase todo");w.geometry("900x600");t=tk.Text(w,wrap="none",font=("Consolas",9));t.pack(fill="both",expand=True);t.insert("1.0",p.read_text(encoding="utf-8",errors="replace"))
        def save():p.write_text(t.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Rebase todo","Saved. Review carefully before continuing.",parent=w)
        ttk.Button(w,text="Save todo",command=save).pack(anchor="e",padx=8,pady=8)

class GitDescribeCenter(tk.Toplevel):
    """Human-readable version/describe utility for refs and release scripting."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Describe & Version Center");self.geometry("950x620");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.ref=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.ref).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Describe",command=self.refresh).pack(side="left",padx=3);ttk.Button(bar,text="Copy version",command=self.copy).pack(side="left")
        self.out=tk.Text(self,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        r=self.ref.get().strip() or "HEAD"
        values=[]
        for label,args in [("Nearest annotated tag",["describe","--tags","--always",r]),("Long form",["describe","--tags","--always","--long","--dirty",r]),("Exact tag",["describe","--tags","--exact-match",r])]:
            try:v=git(self.repo,*args)
            except HANDLED_EXCEPTIONS:v="No exact tag" if label=="Exact tag" else "Unavailable"
            values.append((label,v))
        self.version=values[1][1];text="GIT DESCRIBE\n"+"="*72+"\n\n"+"\n\n".join(f"{k}:\n  {v}" for k,v in values);self.out.delete("1.0","end");self.out.insert("1.0",text)
    def copy(self):self.clipboard_clear();self.clipboard_append(getattr(self,"version",""));messagebox.showinfo("Describe","Copied long-form version string.",parent=self)

class GitWorktreeRepairCenter(tk.Toplevel):
    """Inspect and repair worktree metadata after folders move or disappear."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Worktree Repair Center");self.geometry("1100x710");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Repair metadata",self.repair),("Prune dry-run",self.preview),("Prune stale metadata",self.prune)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Repair adjusts worktree administrative metadata. Prune removes stale records only after a dry-run/confirmation.",padding=8).pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"worktree","list","--porcelain")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def repair(self):
        try:messagebox.showinfo("Worktree repair",git(self.repo,"worktree","repair"),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Worktree repair",str(e),parent=self)
    def preview(self):
        try:v=git(self.repo,"worktree","prune","--dry-run","--verbose")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","PRUNE DRY RUN\n"+"="*72+"\n"+v)
    def prune(self):
        self.preview()
        if messagebox.askyesno("Prune worktrees","Remove worktree entries Git reports as stale?",parent=self):
            try:messagebox.showinfo("Prune",git(self.repo,"worktree","prune","--verbose"),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Prune",str(e),parent=self)

class TagManagerPro(tk.Toplevel):
    """Create, inspect, sign, push and safely delete local/remote tags."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Tag Manager Pro");self.geometry("1180x760");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.name=tk.StringVar();self.target=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.name,width=24).pack(side="left");ttk.Entry(bar,textvariable=self.target,width=18).pack(side="left",padx=4)
        for t,c in [("Create annotated",self.create),("Create signed",self.sign),("Push selected",self.push),("Verify signature",self.verify),("Delete local",self.delete_local),("Delete remote",self.delete_remote),("Refresh",self.refresh)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("tag","type","target","date","subject"),show="headings")
        for c,t,w in [("tag","Tag",250),("type","Type",100),("target","Target",100),("date","Date",150),("subject","Subject",480)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def refresh(self):
        raw=git(self.repo,"for-each-ref","--sort=-creatordate","--format=%(refname:short)%09%(objecttype)%09%(objectname:short)%09%(creatordate:iso8601)%09%(subject)","refs/tags/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",4)
            if len(p)==5:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[0],"Annotated" if p[1]=="tag" else "Lightweight",p[2],p[3],p[4]))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def details(self):
        t=self.selected()
        if t:
            try:v=git(self.repo,"show","--stat","--decorate",t)
            except HANDLED_EXCEPTIONS as e:v=str(e)
            self.out.delete("1.0","end");self.out.insert("1.0",v)
    def create(self):
        n=self.name.get().strip();target=self.target.get().strip() or "HEAD"
        if n:
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-a",n,target,"-m",n),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Tag",str(e),parent=self)
    def sign(self):
        n=self.name.get().strip();target=self.target.get().strip() or "HEAD"
        if n:
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-s",n,target,"-m",n),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Tag",str(e),parent=self)
    def push(self):
        t=self.selected()
        if t and messagebox.askyesno("Push tag",f"Push {t} to origin?",parent=self):
            try:messagebox.showinfo("Tag",git(self.repo,"push","origin",f"refs/tags/{t}"),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Tag",str(e),parent=self)
    def verify(self):
        t=self.selected()
        if t:
            try:v=git(self.repo,"tag","-v",t)
            except HANDLED_EXCEPTIONS as e:v=str(e)
            self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete_local(self):
        t=self.selected()
        if t and messagebox.askyesno("Delete local tag",f"Delete local tag {t}?",parent=self):
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-d",t),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Tag",str(e),parent=self)
    def delete_remote(self):
        t=self.selected()
        if not t:return
        typed=simpledialog.askstring("Delete remote tag",f"Delete refs/tags/{t} from origin. Type the tag exactly:",parent=self)
        if typed==t:
            try:messagebox.showinfo("Tag",git(self.repo,"push","origin",f":refs/tags/{t}"),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Tag",str(e),parent=self)
