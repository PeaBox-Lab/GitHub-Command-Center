"""GitHub Command Center feature windows.

Extracted in v3.73 to keep the application shell independently maintainable.
"""
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.command_gateway import GitError, git

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
        except Exception as e:v=str(e)
        unique=sorted(set(v.splitlines()),key=str.lower);self.ids.delete("1.0","end");self.ids.insert("1.0","\n".join(unique));self.load()
    def load(self):
        self.editor.delete("1.0","end");self.editor.insert("1.0",self.mailmap.read_text(encoding="utf-8",errors="replace") if self.mailmap.exists() else "# Canonical Name <canonical@email> <alternate@email>\n")
    def save(self):
        self.mailmap.write_text(self.editor.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Mailmap","Saved .mailmap. Review and commit it for shared canonical reporting.",parent=self);self.preview()
    def preview(self):
        try:v=git(self.repo,"shortlog","-sne","--all","--use-mailmap")
        except Exception as e:v=str(e)
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
        show=subprocess.run(["git","show","--pretty=format:",ref],cwd=self.repo,capture_output=True,timeout=120)
        if show.returncode:raise GitError(show.stderr.decode("utf-8",errors="replace"))
        pid=subprocess.run(["git","patch-id","--stable"],cwd=self.repo,input=show.stdout,capture_output=True,timeout=120)
        if pid.returncode:raise GitError(pid.stderr.decode("utf-8",errors="replace"))
        return pid.stdout.decode("utf-8",errors="replace").split()[0]
    def compare(self):
        try:
            pa=self.patch_id(self.a.get().strip());pb=self.patch_id(self.b.get().strip());v=f"PATCH ID COMPARISON\n{'='*72}\n{self.a.get()}: {pa}\n{self.b.get()}: {pb}\n\nResult: {'EQUIVALENT CHANGES' if pa==pb else 'DIFFERENT CHANGES'}"
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def range_check(self):
        a=self.a.get().strip();b=self.b.get().strip()
        try:v=git(self.repo,"cherry","-v",a,b)
        except Exception as e:v=str(e)
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
            except:continue
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
        except Exception as e:return "ERROR: "+str(e)
    def refresh(self):
        refs=self.safe("show-ref","--head","--dereference");head=self.safe("symbolic-ref","-q","HEAD");origin_head=self.safe("symbolic-ref","-q","refs/remotes/origin/HEAD");verify=self.safe("fsck","--connectivity-only","--no-dangling");report=f"REF CONSISTENCY\n{'='*72}\nHEAD symbolic ref: {head}\nOrigin default ref: {origin_head}\n\nCONNECTIVITY\n{verify}\n\nREFS\n{refs}"
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def fetch(self):
        try:messagebox.showinfo("Refs",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Refs",str(e),parent=self)

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
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def create(self):
        import re
        b=self.base.get().strip();n=self.name.get().strip()
        if not n or not re.match(r"^[A-Za-z0-9._/-]+$",n):return messagebox.showwarning("Release branch","Enter a valid branch name.",parent=self)
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Release branch","Commit or stash local changes first.",parent=self)
        try:git(self.repo,"rev-parse","--verify",b)
        except Exception as e:return messagebox.showerror("Release branch",str(e),parent=self)
        if messagebox.askyesno("Release branch",f"Create and switch to {n} from {b}?",parent=self):
            try:messagebox.showinfo("Release branch",git(self.repo,"switch","-c",n,b),parent=self)
            except Exception as e:messagebox.showerror("Release branch",str(e),parent=self)

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
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def switch(self):
        b=self.branch.get().strip()
        if b:
            try:messagebox.showinfo("Switch",git(self.repo,"switch",b),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Switch",str(e),parent=self)
    def create(self):
        b=self.branch.get().strip()
        if b:
            try:messagebox.showinfo("Switch",git(self.repo,"switch","-c",b),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Switch",str(e),parent=self)
    def restore(self,staged):
        p=self.path.get().strip();src=self.source.get().strip() or "HEAD"
        if not p:return
        try:preview=git(self.repo,"diff","--",p)
        except Exception as e:preview=str(e)
        if not messagebox.askyesno("Restore path",f"Restore {p} from {src}?\n\nCurrent diff preview:\n{preview[:1600]}",parent=self):return
        args=["restore",f"--source={src}"]+(["--staged","--worktree"] if staged else ["--worktree"])+["--",p]
        try:messagebox.showinfo("Restore",git(self.repo,*args),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Restore",str(e),parent=self)

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
            except:conf=""
            v=f"ACTIVE REBASE: {state}\n{'='*72}\n\n"+"\n\n".join(files)+f"\n\nUNRESOLVED FILES\n{conf}"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def cmd(self,a):
        try:messagebox.showinfo("Rebase",git(self.repo,"rebase",a),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Rebase",str(e),parent=self)
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
            except Exception:v="No exact tag" if label=="Exact tag" else "Unavailable"
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
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def repair(self):
        try:messagebox.showinfo("Worktree repair",git(self.repo,"worktree","repair"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree repair",str(e),parent=self)
    def preview(self):
        try:v=git(self.repo,"worktree","prune","--dry-run","--verbose")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","PRUNE DRY RUN\n"+"="*72+"\n"+v)
    def prune(self):
        self.preview()
        if messagebox.askyesno("Prune worktrees","Remove worktree entries Git reports as stale?",parent=self):
            try:messagebox.showinfo("Prune",git(self.repo,"worktree","prune","--verbose"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Prune",str(e),parent=self)

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
            except Exception as e:v=str(e)
            self.out.delete("1.0","end");self.out.insert("1.0",v)
    def create(self):
        n=self.name.get().strip();target=self.target.get().strip() or "HEAD"
        if n:
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-a",n,target,"-m",n),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Tag",str(e),parent=self)
    def sign(self):
        n=self.name.get().strip();target=self.target.get().strip() or "HEAD"
        if n:
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-s",n,target,"-m",n),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Tag",str(e),parent=self)
    def push(self):
        t=self.selected()
        if t and messagebox.askyesno("Push tag",f"Push {t} to origin?",parent=self):
            try:messagebox.showinfo("Tag",git(self.repo,"push","origin",f"refs/tags/{t}"),parent=self)
            except Exception as e:messagebox.showerror("Tag",str(e),parent=self)
    def verify(self):
        t=self.selected()
        if t:
            try:v=git(self.repo,"tag","-v",t)
            except Exception as e:v=str(e)
            self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete_local(self):
        t=self.selected()
        if t and messagebox.askyesno("Delete local tag",f"Delete local tag {t}?",parent=self):
            try:messagebox.showinfo("Tag",git(self.repo,"tag","-d",t),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Tag",str(e),parent=self)
    def delete_remote(self):
        t=self.selected()
        if not t:return
        typed=simpledialog.askstring("Delete remote tag",f"Delete refs/tags/{t} from origin. Type the tag exactly:",parent=self)
        if typed==t:
            try:messagebox.showinfo("Tag",git(self.repo,"push","origin",f":refs/tags/{t}"),parent=self)
            except Exception as e:messagebox.showerror("Tag",str(e),parent=self)

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
        if p:Path(p).write_text(self.report,encoding="utf-8")

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
        if p:Path(p).write_text(self.report,encoding="utf-8")

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

class MergeCommitRevertCenter(tk.Toplevel):
    """Safely revert a merge commit by explicitly selecting its mainline parent."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Commit Revert Center");self.geometry("1180x750");self.rows=[];self._build();self.load()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.mainline=tk.IntVar(value=1);ttk.Label(bar,text="Mainline parent").pack(side="left");ttk.Spinbox(bar,from_=1,to=8,textvariable=self.mainline,width=5).pack(side="left",padx=4)
        for t,c in [("Refresh",self.load),("Inspect parents",self.inspect),("Preview revert",self.preview),("Execute protected revert",self.execute),("Continue",lambda:self.control("--continue")),("Abort",lambda:self.control("--abort"))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("hash","date","author","parents","subject"),show="headings")
        for c,t,w in [("hash","Merge",100),("date","Date",110),("author","Author",170),("parents","Parents",190),("subject","Subject",510)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="Mainline parent defines which side of the merge is retained. Review parent commits and preview carefully. A safety branch is created before revert.",padding=8).pack(fill="x")
    def load(self):
        raw=git(self.repo,"log","--all","--merges","-200","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%P%x1f%s");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[1],p[2],p[3]," ".join(x[:8] for x in p[4].split()),p[5]))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        lines=[f"MERGE: {r[0]}\nSUBJECT: {r[5]}\n"]
        for i,parent in enumerate(r[4].split(),1):
            try:lines.append(f"PARENT {i}\n"+git(self.repo,"show","-s","--date=iso-strict","--pretty=fuller",parent))
            except Exception as e:lines.append(str(e))
        self.out.delete("1.0","end");self.out.insert("1.0","\n\n".join(lines))
    def preview(self):
        r=self.selected()
        if not r:return
        m=int(self.mainline.get())
        if m<1 or m>len(r[4].split()):return messagebox.showwarning("Merge revert","Selected mainline parent does not exist.",parent=self)
        try:v=git(self.repo,"diff",f"{r[0]}^{m}",r[0],"--stat")+"\n\nREVERT WOULD INVERT THIS MERGE-SIDE CHANGE\n"+git(self.repo,"diff",f"{r[0]}^{m}",r[0],"--name-status")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def execute(self):
        import datetime
        r=self.selected()
        if not r:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Merge revert","Commit or stash local changes first.",parent=self)
        m=int(self.mainline.get())
        if m<1 or m>len(r[4].split()):return messagebox.showwarning("Merge revert","Invalid mainline parent.",parent=self)
        backup=f"gccc-backup/pre-merge-revert-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}";git(self.repo,"branch",backup)
        if not messagebox.askyesno("Revert merge",f"Safety branch: {backup}\n\nRevert merge {r[1]} using mainline parent {m}?",parent=self):return
        try:messagebox.showinfo("Merge revert",git(self.repo,"revert","-m",str(m),"--no-edit",r[0]),parent=self)
        except Exception as e:messagebox.showwarning("Merge revert",f"Revert paused or failed. Resolve conflicts and Continue, or Abort.\n\n{e}",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Revert",git(self.repo,"revert",arg),parent=self)
        except Exception as e:messagebox.showerror("Revert",str(e),parent=self)

class DiffAlgorithmCenter(tk.Toplevel):
    """Compare Git diff algorithms and word-diff output for a selected ref/path."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Diff Algorithm Lab");self.geometry("1160x740");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.left=tk.StringVar();self.right=tk.StringVar(value="HEAD");self.path=tk.StringVar();self.algorithm=tk.StringVar(value="histogram");self.words=tk.BooleanVar()
        ttk.Entry(bar,textvariable=self.left,width=20).pack(side="left");ttk.Entry(bar,textvariable=self.right,width=20).pack(side="left",padx=3);ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Combobox(bar,textvariable=self.algorithm,values=["myers","minimal","patience","histogram"],state="readonly",width=12).pack(side="left",padx=3);ttk.Checkbutton(bar,text="Word diff",variable=self.words).pack(side="left");ttk.Button(bar,text="Run diff",command=self.run).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def run(self):
        args=["diff",f"--diff-algorithm={self.algorithm.get()}"]
        if self.words.get():args.append("--word-diff=plain")
        l=self.left.get().strip();r=self.right.get().strip()
        if l and r:args += [l,r]
        elif r and r!="HEAD":args.append(r)
        p=self.path.get().strip()
        if p:args += ["--",p]
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class SubtreeCenter(tk.Toplevel):
    """Manage vendored subprojects with git subtree."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Subtree Center");self.geometry("1080x700");self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.prefix=tk.StringVar(value="vendor/project");self.remote=tk.StringVar();self.ref=tk.StringVar(value="main");self.squash=tk.BooleanVar(value=True)
        ttk.Entry(bar,textvariable=self.prefix,width=25).pack(side="left");ttk.Entry(bar,textvariable=self.remote).pack(side="left",fill="x",expand=True,padx=4);ttk.Entry(bar,textvariable=self.ref,width=16).pack(side="left");ttk.Checkbutton(bar,text="Squash",variable=self.squash).pack(side="left",padx=4)
        for t,c in [("Add subtree",self.add),("Pull subtree",self.pull),("Push subtree",self.push),("Split branch",self.split)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Subtree operations can create commits. Commit or stash local changes first. Squash keeps imported history compact; non-squash preserves the subproject history.",padding=8).pack(fill="x")
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def args(self,verb):
        args=["subtree",verb,f"--prefix={self.prefix.get().strip()}"]
        if verb in ("add","pull","push"):args += [self.remote.get().strip(),self.ref.get().strip()]
        if self.squash.get() and verb in ("add","pull"):args.append("--squash")
        return args
    def run(self,verb,confirm):
        if not self.clean():return messagebox.showwarning("Subtree","Commit or stash changes first.",parent=self)
        if not self.prefix.get().strip() or (verb in ("add","pull","push") and not self.remote.get().strip()):return
        if not messagebox.askyesno("Git subtree",confirm,parent=self):return
        try:v=git(self.repo,*self.args(verb));self.out.delete("1.0","end");self.out.insert("1.0",v);messagebox.showinfo("Git subtree",v,parent=self)
        except Exception as e:messagebox.showerror("Git subtree",str(e),parent=self)
    def add(self):self.run("add",f"Add subtree at {self.prefix.get()} from {self.remote.get()} {self.ref.get()}?")
    def pull(self):self.run("pull",f"Pull subtree updates into {self.prefix.get()}?")
    def push(self):self.run("push",f"Push subtree {self.prefix.get()} to {self.remote.get()} {self.ref.get()}?")
    def split(self):
        branch=simpledialog.askstring("Subtree split","New local branch for split history:",parent=self)
        if branch:
            try:v=git(self.repo,"subtree","split",f"--prefix={self.prefix.get().strip()}",f"--branch={branch}");self.out.delete("1.0","end");self.out.insert("1.0",v)
            except Exception as e:messagebox.showerror("Subtree split",str(e),parent=self)

class GitFilterRepoAdvisor(tk.Toplevel):
    """Analyze history-rewrite candidates and prepare safe git-filter-repo guidance."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("History Rewrite Advisor");self.geometry("1120x740");self._build();self.analyze()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.path=tk.StringVar();self.replacement=tk.StringVar();ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.replacement,width=28).pack(side="left",padx=4)
        for t,c in [("Analyze path history",self.analyze),("Check git-filter-repo",self.check_tool),("Generate command",self.generate)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="This center does not execute history rewriting. It produces evidence and a reviewable command because rewriting published history affects every clone and requires coordinated force-with-lease pushes.",padding=8,foreground="#b91c1c").pack(fill="x")
    def analyze(self):
        p=self.path.get().strip()
        if not p:self.out.delete("1.0","end");self.out.insert("1.0","Enter a path to analyze across history.");return
        try:
            log=git(self.repo,"log","--all","--follow","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s","--",p);sizes=git(self.repo,"rev-list","--objects","--all");hits=[x for x in sizes.splitlines() if x.endswith(" "+p) or (" " in x and x.split(" ",1)[1]==p)]
            v=f"PATH HISTORY ANALYSIS\n{'='*72}\nPath: {p}\nObject references: {len(hits)}\n\nCOMMITS\n{log}\n\nBefore rewriting:\n1. Create and verify a full Git bundle.\n2. Coordinate with collaborators.\n3. Remove/rotate any exposed secret.\n4. Rewrite in a disposable clone.\n5. Verify refs and run fsck.\n6. Push with force-with-lease deliberately."
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def check_tool(self):
        try:r=subprocess.run(["git-filter-repo","--version"],text=True,capture_output=True,timeout=30,encoding="utf-8",errors="replace");v=(r.stdout+r.stderr).strip() or f"Exit {r.returncode}"
        except Exception as e:v="git-filter-repo not found. Install it from its official distribution before using generated commands.\n\n"+str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def generate(self):
        import shlex
        p=self.path.get().strip()
        if not p:return
        if self.replacement.get().strip():cmd=["git-filter-repo","--path",p,"--path-rename",f"{p}:{self.replacement.get().strip()}"]
        else:cmd=["git-filter-repo","--path",p,"--invert-paths"]
        v="REVIEWABLE COMMAND - NOT EXECUTED\n"+"="*72+"\n"+" ".join(shlex.quote(x) for x in cmd)+"\n\nRun only in a disposable, backed-up clone after reviewing the impact."
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class AttributesAuditCenter(tk.Toplevel):
    """Audit effective attributes for tracked paths and find missing binary/LFS rules."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Attributes Audit Center");self.geometry("1160x740");self.rows=[];self._build();self.scan()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.limit=tk.IntVar(value=5000);ttk.Label(bar,text="Max files").pack(side="left");ttk.Spinbox(bar,from_=100,to=50000,increment=100,textvariable=self.limit,width=8).pack(side="left",padx=4);ttk.Button(bar,text="Scan",command=self.scan).pack(side="left");ttk.Button(bar,text="Export report",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Open Ignore & Attributes Studio",command=lambda:IgnoreAttributesStudio(self,self.repo)).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("path","text","eol","diff","merge","filter"),show="headings")
        for c,t,w in [("path","Path",480),("text","Text",80),("eol","EOL",80),("diff","Diff",100),("merge","Merge",100),("filter","Filter/LFS",140)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def scan(self):
        files=git(self.repo,"ls-files").splitlines()[:int(self.limit.get())];self.rows=[];self.tree.delete(*self.tree.get_children());report=[]
        for f in files:
            try:raw=git(self.repo,"check-attr","text","eol","diff","merge","filter","--",f);attrs={}
            except:continue
            for line in raw.splitlines():
                p=line.split(": ",2)
                if len(p)==3:attrs[p[1]]=p[2]
            suffix=Path(f).suffix.lower();interesting=suffix in (".png",".jpg",".jpeg",".gif",".zip",".pdf",".exe",".dll",".bin") or attrs.get("filter") not in (None,"unspecified")
            if interesting:
                r=(f,attrs.get("text",""),attrs.get("eol",""),attrs.get("diff",""),attrs.get("merge",""),attrs.get("filter",""));self.rows.append(r);self.tree.insert("","end",values=r);report.append(" | ".join(r))
        self.report="ATTRIBUTES AUDIT\n"+"="*72+"\n"+"\n".join(report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="attributes-audit.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class GitRangeDiffCenter(tk.Toplevel):
    """Compare two commit series before and after rebase using git range-diff."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Range-Diff Center");self.geometry("1160x740");self._build();self.run()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.old=tk.StringVar(value="main..HEAD~1");self.new=tk.StringVar(value="main..HEAD");ttk.Entry(bar,textvariable=self.old).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.new).pack(side="left",fill="x",expand=True,padx=4);ttk.Button(bar,text="Compare series",command=self.run).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Use range-diff after rebase to compare the old patch series with the rewritten patch series. It compares changes, not only commit hashes.",padding=8).pack(fill="x")
    def run(self):
        try:self.report=git(self.repo,"range-diff",self.old.get().strip(),self.new.get().strip())
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="range-diff.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class RefspecLabCenter(tk.Toplevel):
    """Inspect remote refspecs and generate explicit fetch/push commands."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Refspec Lab");self.geometry("1100x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.remote=tk.StringVar(value="origin");self.src=tk.StringVar(value="refs/heads/main");self.dst=tk.StringVar(value="refs/remotes/origin/main");ttk.Entry(bar,textvariable=self.remote,width=15).pack(side="left");ttk.Entry(bar,textvariable=self.src).pack(side="left",fill="x",expand=True,padx=3);ttk.Entry(bar,textvariable=self.dst).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Preview fetch",command=self.preview_fetch).pack(side="left",padx=3);ttk.Button(bar,text="Preview push",command=self.preview_push).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Previews use --dry-run. This center does not save custom refspecs automatically; use Git Configuration Center after reviewing the mapping.",padding=8).pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"config","--get-regexp",r"^remote\..*\.(fetch|push)$")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","CONFIGURED REFSPECS\n"+"="*72+"\n"+v)
    def preview_fetch(self):
        spec=f"{self.src.get().strip()}:{self.dst.get().strip()}"
        try:v=git(self.repo,"fetch","--dry-run",self.remote.get().strip(),spec)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",f"FETCH DRY RUN\n{self.remote.get()} {spec}\n\n{v}")
    def preview_push(self):
        spec=f"{self.src.get().strip()}:{self.dst.get().strip()}"
        try:v=git(self.repo,"push","--dry-run",self.remote.get().strip(),spec)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",f"PUSH DRY RUN\n{self.remote.get()} {spec}\n\n{v}")

class GitNotesMergeCenter(tk.Toplevel):
    """Inspect and merge Git notes refs using configured notes merge strategies."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Notes Merge Center");self.geometry("1050x680");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.local=tk.StringVar(value="commits");self.other=tk.StringVar(value="refs/notes/review");self.strategy=tk.StringVar(value="cat_sort_uniq");ttk.Entry(bar,textvariable=self.local,width=20).pack(side="left");ttk.Entry(bar,textvariable=self.other).pack(side="left",fill="x",expand=True,padx=4);ttk.Combobox(bar,textvariable=self.strategy,values=["manual","ours","theirs","union","cat_sort_uniq"],state="readonly",width=15).pack(side="left")
        for t,c in [("Refresh",self.refresh),("Merge notes ref",self.merge),("Commit merge",lambda:self.control("--commit")),("Abort merge",lambda:self.control("--abort"))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Notes merges affect only the selected notes ref, not commit IDs. Manual conflicts may require editing the notes merge worktree before commit/abort.",padding=8).pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"for-each-ref","--format=%(refname)%09%(objectname:short)%09%(subject)","refs/notes/")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","NOTES REFS\n"+"="*72+"\n"+v)
    def merge(self):
        local=self.local.get().strip();other=self.other.get().strip();strategy=self.strategy.get()
        if not local or not other:return
        if not messagebox.askyesno("Merge notes",f"Merge {other} into refs/notes/{local} using {strategy}?",parent=self):return
        try:messagebox.showinfo("Notes merge",git(self.repo,"notes",f"--ref={local}","merge",f"-s{strategy}",other),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Notes merge",str(e),parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Notes merge",git(self.repo,"notes",f"--ref={self.local.get().strip()}","merge",arg),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Notes merge",str(e),parent=self)

class MergeStrategyLabCenter(tk.Toplevel):
    """Preview Git merge strategies and strategy options before a real merge."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Strategy Lab");self.geometry("1120x720");self._build();self.preview()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.target=tk.StringVar();self.strategy=tk.StringVar(value="ort");self.option=tk.StringVar(value="")
        ttk.Entry(bar,textvariable=self.target).pack(side="left",fill="x",expand=True);ttk.Combobox(bar,textvariable=self.strategy,values=["ort","recursive","resolve","octopus","ours","subtree"],state="readonly",width=12).pack(side="left",padx=4);ttk.Combobox(bar,textvariable=self.option,values=["","ours","theirs","patience","histogram","ignore-space-change","renormalize"],width=20).pack(side="left")
        ttk.Button(bar,text="Preview",command=self.preview).pack(side="left",padx=3);ttk.Button(bar,text="Perform no-commit merge",command=self.merge).pack(side="left");ttk.Button(bar,text="Abort",command=self.abort).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Preview uses merge-base and merge-tree. A real merge uses --no-commit --no-ff so you can inspect before committing. Clean tree required.",padding=8).pack(fill="x")
    def preview(self):
        t=self.target.get().strip()
        if not t:self.out.delete("1.0","end");self.out.insert("1.0","Enter a branch or ref to preview.");return
        try:base=git(self.repo,"merge-base","HEAD",t);v=git(self.repo,"merge-tree",base,"HEAD",t);text=f"MERGE STRATEGY PREVIEW\n{'='*72}\nTarget: {t}\nStrategy: {self.strategy.get()}\nOption: {self.option.get() or 'default'}\nMerge base: {base}\n\n{v}"
        except Exception as e:text=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",text)
    def merge(self):
        t=self.target.get().strip()
        if not t:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Merge","Commit or stash changes first.",parent=self)
        args=["merge","--no-commit","--no-ff","-s",self.strategy.get()]
        if self.option.get().strip():args += ["-X",self.option.get().strip()]
        args.append(t)
        if messagebox.askyesno("Merge strategy",f"Start a no-commit merge of {t} using {self.strategy.get()}?",parent=self):
            try:messagebox.showinfo("Merge",git(self.repo,*args),parent=self)
            except Exception as e:messagebox.showerror("Merge",str(e),parent=self)
    def abort(self):
        try:messagebox.showinfo("Merge",git(self.repo,"merge","--abort"),parent=self)
        except Exception as e:messagebox.showerror("Merge",str(e),parent=self)

class ConfigIncludeCenter(tk.Toplevel):
    """Inspect Git config include/includeIf rules and their resolved origins."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Config Include Inspector");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Open Git Configuration",command=lambda:GitConfigCenter(self,self.repo)).pack(side="left",padx=3);ttk.Button(bar,text="Export",command=self.export).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:incs=git(self.repo,"config","--show-origin","--show-scope","--get-regexp",r"^(include\.path|includeIf\..*\.path)$")
        except Exception as e:incs="No include rules found or Git returned:\n"+str(e)
        try:effective=git(self.repo,"config","--list","--show-origin","--show-scope","--includes")
        except Exception as e:effective=str(e)
        self.report="CONFIG INCLUDE RULES\n"+"="*72+"\n"+incs+"\n\nEFFECTIVE CONFIG WITH INCLUDES\n"+"="*72+"\n"+effective;self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="git-config-includes.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class PackInventoryCenter(tk.Toplevel):
    """Inspect pack indexes, object counts and largest packed blobs without modifying history."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Pack Inventory Center");self.geometry("1160x740");self._build();self.scan()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.limit=tk.IntVar(value=30);ttk.Label(bar,text="Largest blobs").pack(side="left");ttk.Spinbox(bar,from_=10,to=500,increment=10,textvariable=self.limit,width=7).pack(side="left",padx=4);ttk.Button(bar,text="Scan packs",command=self.scan).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Open Maintenance",command=lambda:MaintenanceCenter(self,self.repo)).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Read-only analysis. Packed-object sizes are compressed storage approximations; use History Rewrite Advisor before any historical cleanup.",padding=8).pack(fill="x")
    def scan(self):
        gd=Path(git(self.repo,"rev-parse","--git-dir"));gd=(Path(self.repo)/gd).resolve() if not gd.is_absolute() else gd;idxs=list((gd/"objects"/"pack").glob("*.idx"));entries=[]
        for idx in idxs:
            try:raw=git(self.repo,"verify-pack","-v",str(idx))
            except:continue
            for line in raw.splitlines():
                p=line.split()
                if len(p)>=5 and len(p[0])>=40 and p[1]=="blob" and p[2].isdigit():entries.append((int(p[2]),p[0],idx.name))
        entries=sorted(entries,reverse=True)[:int(self.limit.get())];report="PACK INVENTORY\n"+"="*72+f"\nPack indexes: {len(idxs)}\n\n"+git(self.repo,"count-objects","-vH")+"\n\nLARGEST PACKED BLOBS\n"
        for size,sha,pack in entries:
            try:paths=git(self.repo,"rev-list","--objects","--all");path=next((x.split(" ",1)[1] for x in paths.splitlines() if x.startswith(sha+" ")),"(path not directly mapped)")
            except:path=""
            report+=f"{size/1024/1024:9.2f} MB  {sha[:12]}  {path}  [{pack}]\n"
        self.report=report;self.out.delete("1.0","end");self.out.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="pack-inventory.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class ChangeStatisticsCenter(tk.Toplevel):
    """Analyze change volume, file types, authors, and churn for a revision range."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Change Statistics Center");self.geometry("1160x740");self._build();self.analyze()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.base=tk.StringVar(value="HEAD~20");self.tip=tk.StringVar(value="HEAD")
        ttk.Entry(bar,textvariable=self.base,width=24).pack(side="left");ttk.Entry(bar,textvariable=self.tip,width=24).pack(side="left",padx=4);ttk.Button(bar,text="Analyze",command=self.analyze).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def analyze(self):
        a=self.base.get().strip();b=self.tip.get().strip();spec=f"{a}..{b}"
        try:
            commits=git(self.repo,"rev-list","--count",spec);authors=git(self.repo,"shortlog","-sne",spec);num=git(self.repo,"diff","--numstat",a,b);files=adds=dels=0;ext={};churn=[]
            for line in num.splitlines():
                p=line.split("\t")
                if len(p)>=3:
                    files+=1;ad=int(p[0]) if p[0].isdigit() else 0;de=int(p[1]) if p[1].isdigit() else 0;adds+=ad;dels+=de;path=p[2];key=Path(path).suffix.lower() or "(no extension)";ext[key]=ext.get(key,0)+ad+de;churn.append((ad+de,ad,de,path))
            report=f"CHANGE STATISTICS\n{'='*76}\nRange: {spec}\nCommits: {commits}\nFiles changed: {files}\nAdditions: {adds}\nDeletions: {dels}\nTotal churn: {adds+dels}\n\nAUTHORS\n{authors}\n\nCHURN BY EXTENSION\n"
            for k,v in sorted(ext.items(),key=lambda x:-x[1]):report+=f"{k:<18}{v:>10}\n"
            report+="\nHIGHEST-CHURN FILES\n"
            for total,ad,de,path in sorted(churn,reverse=True)[:40]:report+=f"{total:>8}  +{ad:<7} -{de:<7} {path}\n"
            self.report=report
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="change-statistics.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class ConflictStageExplorer(tk.Toplevel):
    """Inspect stage-1/base, stage-2/ours, and stage-3/theirs blobs for unresolved paths."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Conflict Stage Explorer");self.geometry("1380x800");self.paths=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Use ours",command=lambda:self.use("--ours")).pack(side="left",padx=3);ttk.Button(bar,text="Use theirs",command=lambda:self.use("--theirs")).pack(side="left");ttk.Button(bar,text="Stage resolved",command=self.stage).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=1);pane.add(right,weight=5)
        self.list=tk.Listbox(left,font=("Consolas",9));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.load())
        nb=ttk.Notebook(right);nb.pack(fill="both",expand=True);self.views={}
        for name in ("BASE stage 1","OURS stage 2","THEIRS stage 3","WORKTREE"):
            f=ttk.Frame(nb);nb.add(f,text=name);t=tk.Text(f,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");t.pack(fill="both",expand=True);self.views[name]=t
        ttk.Label(self,text="Stage views are read-only. Use ours/theirs only when that complete side is intended; otherwise edit the working file using the main conflict resolver.",padding=8).pack(fill="x")
    def refresh(self):
        try:raw=git(self.repo,"diff","--name-only","--diff-filter=U")
        except:raw=""
        self.paths=[x for x in raw.splitlines() if x and x!="Completed successfully."];self.list.delete(0,"end");[self.list.insert("end",p) for p in self.paths]
        if self.paths:self.list.selection_set(0);self.load()
    def selected(self):
        s=self.list.curselection();return self.paths[s[0]] if s else None
    def blob(self,stage,path):
        r=subprocess.run(["git","show",f":{stage}:{path}"],cwd=self.repo,capture_output=True,timeout=120)
        return r.stdout.decode("utf-8",errors="replace") if r.returncode==0 else "(stage unavailable or binary)"
    def load(self):
        p=self.selected()
        if not p:return
        values={"BASE stage 1":self.blob(1,p),"OURS stage 2":self.blob(2,p),"THEIRS stage 3":self.blob(3,p)}
        try:values["WORKTREE"]=(Path(self.repo)/p).read_text(encoding="utf-8",errors="replace")
        except:values["WORKTREE"]="(working file unavailable or binary)"
        for n,v in values.items():self.views[n].delete("1.0","end");self.views[n].insert("1.0",v)
    def use(self,side):
        p=self.selected()
        if p and messagebox.askyesno("Resolve conflict",f"Replace the working file with {side[2:]} for {p}?",parent=self):
            try:messagebox.showinfo("Conflict",git(self.repo,"checkout",side,"--",p),parent=self);self.load()
            except Exception as e:messagebox.showerror("Conflict",str(e),parent=self)
    def stage(self):
        p=self.selected()
        if p:
            try:messagebox.showinfo("Conflict",git(self.repo,"add","--",p),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Conflict",str(e),parent=self)

class BranchRenamePlanner(tk.Toplevel):
    """Plan local and optional remote branch rename with upstream repair."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Branch Rename Planner");self.geometry("1000x660");self._build();self.preview()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.old=tk.StringVar();self.new=tk.StringVar();self.remote=tk.StringVar(value="origin");self.update_remote=tk.BooleanVar(value=True)
        for i,(label,var) in enumerate((("Current/local branch",self.old),("New branch name",self.new),("Remote",self.remote))):ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=6);ttk.Entry(f,textvariable=var).grid(row=i,column=1,sticky="ew",padx=8)
        ttk.Checkbutton(f,text="Publish new remote branch and remove old remote branch",variable=self.update_remote).grid(row=3,column=1,sticky="w",pady=6);f.columnconfigure(1,weight=1)
        ttk.Button(f,text="Preview",command=self.preview).grid(row=4,column=0,pady=8);ttk.Button(f,text="Execute protected rename",command=self.execute,style="Accent.TButton").grid(row=4,column=1,sticky="e",pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=5,column=0,columnspan=2,sticky="nsew");f.rowconfigure(5,weight=1)
    def preview(self):
        try:
            current=git(self.repo,"branch","--show-current")
            if not self.old.get():self.old.set(current)
            up=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name",f"{self.old.get()}@{{u}}")
        except Exception as e:up="Not configured: "+str(e)
        v=f"BRANCH RENAME PLAN\n{'='*72}\nOld local: {self.old.get()}\nNew local: {self.new.get() or '(enter a name)'}\nCurrent upstream: {up}\nRemote workflow: {'publish new + delete old' if self.update_remote.get() else 'local only'}\n\nRemote deletion always requires exact typed confirmation."
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def execute(self):
        import re
        old=self.old.get().strip();new=self.new.get().strip();remote=self.remote.get().strip()
        if not old or not new or not re.match(r"^[A-Za-z0-9._/-]+$",new):return messagebox.showwarning("Rename","Enter valid branch names.",parent=self)
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Rename","Commit or stash local changes first.",parent=self)
        if not messagebox.askyesno("Rename branch",f"Rename local branch {old} to {new}?",parent=self):return
        try:
            git(self.repo,"branch","-m",old,new)
            if self.update_remote.get():
                git(self.repo,"push","-u",remote,new);typed=simpledialog.askstring("Delete old remote",f"New branch published. Type the old branch name exactly to delete {remote}/{old}:",parent=self)
                if typed==old:git(self.repo,"push",remote,"--delete",old)
            messagebox.showinfo("Rename","Branch rename workflow completed.",parent=self);self.old.set(new);self.preview()
        except Exception as e:messagebox.showerror("Rename",str(e),parent=self)

class LostFoundCenter(tk.Toplevel):
    """Inspect Git fsck lost-found objects and preserve commits safely."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Lost & Found Center");self.geometry("1180x750");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for text,cmd in [("Run fsck lost-found",self.scan),("Refresh inventory",self.refresh),("Inspect selected",self.inspect),("Create recovery branch",self.recover),("Export report",self.export)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("kind","object","date","subject"),show="headings")
        for c,t,w in [("kind","Kind",100),("object","Object",360),("date","Date",160),("subject","Subject / details",490)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="git fsck --lost-found writes references under .git/lost-found. Recovery creates a normal branch at a selected commit. No object deletion is performed.",padding=8).pack(fill="x")
    def gitdir(self):
        p=Path(git(self.repo,"rev-parse","--git-dir"));return (Path(self.repo)/p).resolve() if not p.is_absolute() else p
    def scan(self):
        try:messagebox.showinfo("Lost & Found",git(self.repo,"fsck","--full","--lost-found","--no-reflogs"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Lost & Found",str(e),parent=self)
    def refresh(self):
        base=self.gitdir()/"lost-found";self.rows=[];self.tree.delete(*self.tree.get_children())
        for kind in ("commit","other"):
            folder=base/kind
            if not folder.exists():continue
            for p in sorted(folder.iterdir()):
                sha=p.name;date=subject=""
                if kind=="commit":
                    try:info=git(self.repo,"show","-s","--date=iso-strict","--pretty=format:%cI%x1f%s",sha).split("\x1f",1);date=info[0];subject=info[1] if len(info)>1 else ""
                    except:pass
                else:subject="Recovered object reference"
                self.rows.append((kind,sha,date,subject));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
        self.report="LOST & FOUND INVENTORY\n"+"="*72+"\n"+"\n".join(" | ".join(r) for r in self.rows)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--patch",r[1]) if r[0]=="commit" else git(self.repo,"cat-file","-p",r[1])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def recover(self):
        import datetime,re
        r=self.selected()
        if not r or r[0]!="commit":return messagebox.showinfo("Recovery","Select a lost commit.",parent=self)
        default=f"recovery/lost-found-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{r[1][:8]}";name=simpledialog.askstring("Recovery branch","New branch name:",initialvalue=default,parent=self)
        if name and re.match(r"^[A-Za-z0-9._/-]+$",name):
            try:messagebox.showinfo("Recovery",git(self.repo,"branch",name,r[1]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Recovery",str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="lost-found-inventory.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class ShallowRepositoryCenter(tk.Toplevel):
    """Inspect and deepen shallow repositories deliberately."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Shallow Repository Center");self.geometry("1010x660");self.depth=tk.IntVar(value=100);self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Label(bar,text="Deepen by").pack(side="left");ttk.Spinbox(bar,from_=1,to=100000,increment=50,textvariable=self.depth,width=9).pack(side="left",padx=4)
        for text,cmd in [("Refresh",self.refresh),("Deepen",self.deepen),("Fetch complete history",self.unshallow),("Fetch tags",self.tags)]:ttk.Button(bar,text=text,command=cmd).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Deepening downloads more history. Unshallow may transfer substantial data and requires confirmation.",padding=8).pack(fill="x")
    def is_shallow(self):return git(self.repo,"rev-parse","--is-shallow-repository").lower()=="true"
    def refresh(self):
        shallow=self.is_shallow();count=git(self.repo,"rev-list","--count","HEAD");boundary=""
        try:boundary=git(self.repo,"rev-list","--boundary","--max-count=30","HEAD")
        except:pass
        v=f"SHALLOW REPOSITORY\n{'='*72}\nShallow: {'Yes' if shallow else 'No'}\nReachable commits from HEAD: {count}\n\nRECENT/BOUNDARY VIEW\n{boundary}"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def deepen(self):
        if not self.is_shallow():return messagebox.showinfo("Shallow repository","Repository already has complete history.",parent=self)
        try:messagebox.showinfo("Deepen",git(self.repo,"fetch",f"--deepen={int(self.depth.get())}"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Deepen",str(e),parent=self)
    def unshallow(self):
        if not self.is_shallow():return messagebox.showinfo("Shallow repository","Repository is not shallow.",parent=self)
        if messagebox.askyesno("Complete history","Fetch complete history for this clone? This may download substantial data.",parent=self):
            try:messagebox.showinfo("Unshallow",git(self.repo,"fetch","--unshallow"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Unshallow",str(e),parent=self)
    def tags(self):
        try:messagebox.showinfo("Tags",git(self.repo,"fetch","--tags"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Tags",str(e),parent=self)

class StatusPorcelainCenter(tk.Toplevel):
    """Explain Git status porcelain v2 records for automation and debugging."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Status Porcelain Explorer");self.geometry("1120x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Copy raw output",command=self.copy).pack(side="left",padx=3);ttk.Button(bar,text="Export",command=self.export).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("record","xy","sub","path","details"),show="headings")
        for c,t,w in [("record","Record",80),("xy","XY",60),("sub","Submodule",100),("path","Path",430),("details","Details",430)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        self.raw=git(self.repo,"status","--porcelain=v2","--branch");self.tree.delete(*self.tree.get_children());headers=[]
        for line in self.raw.splitlines():
            if line.startswith("#"):headers.append(line);continue
            p=line.split(" ")
            rec=p[0] if p else "";xy=p[1] if len(p)>1 and rec in ("1","2","u") else "";sub=p[2] if len(p)>2 and rec in ("1","2","u") else "";path=""
            if rec=="?" or rec=="!":path=line[2:]
            elif rec=="1" and len(p)>=9:path=" ".join(p[8:])
            elif rec=="2" and len(p)>=10:path=" ".join(p[9:]).split("\t",1)[0]
            elif rec=="u" and len(p)>=11:path=" ".join(p[10:])
            self.tree.insert("","end",values=(rec,xy,sub,path,line))
        self.out.delete("1.0","end");self.out.insert("1.0","BRANCH HEADERS\n"+"\n".join(headers)+"\n\nRAW PORCELAIN V2\n"+self.raw)
    def copy(self):self.clipboard_clear();self.clipboard_append(self.raw);messagebox.showinfo("Status","Copied raw porcelain output.",parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="status-porcelain-v2.txt")
        if p:Path(p).write_text(self.raw,encoding="utf-8")

class GitSparseIndexCenter(tk.Toplevel):
    """Inspect and toggle sparse-index support for sparse-checkout repositories."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Sparse Index Center");self.geometry("1010x660");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Enable sparse index",self.enable),("Disable sparse index",self.disable),("Open Sparse Checkout",lambda:SparseCheckoutCenter(self,self.repo))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Sparse index can improve performance in large sparse-checkout repositories. Enable it only when sparse checkout is active and your Git version supports it.",padding=8).pack(fill="x")
    def refresh(self):
        def cfg(k):
            try:return git(self.repo,"config","--get",k)
            except:return "Not set"
        try:sparse=git(self.repo,"sparse-checkout","list")
        except Exception:sparse="Sparse checkout is not active."
        try:gitver=git(self.repo,"--version")
        except Exception as e:gitver=str(e)
        v=f"SPARSE INDEX STATUS\n{'='*72}\n{gitver}\ncore.sparseCheckout: {cfg('core.sparseCheckout')}\nindex.sparse: {cfg('index.sparse')}\n\nSPARSE PATHS\n{sparse}"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def enable(self):
        if not self.clean():return messagebox.showwarning("Sparse index","Commit or stash changes first.",parent=self)
        try:messagebox.showinfo("Sparse index",git(self.repo,"sparse-checkout","reapply","--sparse-index"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Sparse index",str(e),parent=self)
    def disable(self):
        if not self.clean():return messagebox.showwarning("Sparse index","Commit or stash changes first.",parent=self)
        try:messagebox.showinfo("Sparse index",git(self.repo,"sparse-checkout","reapply","--no-sparse-index"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Sparse index",str(e),parent=self)

class ObjectFormatCenter(tk.Toplevel):
    """Inspect repository object/ref storage formats and compatibility-sensitive extensions."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Format Inspector");self.geometry("1040x680");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Open Config Center",command=lambda:GitConfigCenter(self,self.repo)).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Read-only format inspection. Repository format/object format changes require careful compatibility planning and are not modified here.",padding=8).pack(fill="x")
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        fields=[("Git version",self.safe("--version")),("Repository format version",self.safe("config","--get","core.repositoryformatversion")),("Object format",self.safe("rev-parse","--show-object-format")),("Ref storage format",self.safe("rev-parse","--show-ref-format")),("Bare repository",self.safe("rev-parse","--is-bare-repository")),("Shallow repository",self.safe("rev-parse","--is-shallow-repository")),("Common Git dir",self.safe("rev-parse","--git-common-dir")),("Worktree Git dir",self.safe("rev-parse","--git-dir"))]
        ext=self.safe("config","--get-regexp",r"^extensions\.")
        self.report="REPOSITORY FORMAT INSPECTOR\n"+"="*72+"\n\n"+"\n".join(f"{k}: {v}" for k,v in fields)+"\n\nREPOSITORY EXTENSIONS\n"+ext
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-format.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class GitCleanInteractiveCenter(tk.Toplevel):
    """Selective untracked-file cleanup with mandatory preview and explicit selection."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Selective Clean Center");self.geometry("1100x720");self.rows=[];self.include_ignored=tk.BooleanVar();self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Checkbutton(bar,text="Include ignored",variable=self.include_ignored,command=self.refresh).pack(side="left")
        ttk.Button(bar,text="Refresh preview",command=self.refresh).pack(side="left",padx=3);ttk.Button(bar,text="Delete selected",command=self.delete).pack(side="left")
        self.list=tk.Listbox(self,selectmode="extended",font=("Consolas",9));self.list.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Only selected untracked paths are removed. Ignored paths require an additional typed confirmation. Git cannot restore cleaned files.",padding=8).pack(fill="x")
    def refresh(self):
        args=["clean","-nd"]+(["-x"] if self.include_ignored.get() else [])
        try:raw=git(self.repo,*args)
        except Exception as e:raw=str(e)
        self.rows=[];self.list.delete(0,"end")
        for line in raw.splitlines():
            if line.startswith("Would remove "):
                p=line[len("Would remove "):];self.rows.append(p);self.list.insert("end",p)
        self.out.delete("1.0","end");self.out.insert("1.0",f"Previewed paths: {len(self.rows)}\n\n{raw}")
    def delete(self):
        selected=[self.rows[i] for i in self.list.curselection()]
        if not selected:return
        if self.include_ignored.get():
            typed=simpledialog.askstring("Delete ignored paths",f"Selected {len(selected)} path(s), including ignored content. Type DELETE SELECTED to continue:",parent=self)
            if typed!="DELETE SELECTED":return
        elif not messagebox.askyesno("Selective clean",f"Permanently delete {len(selected)} selected untracked path(s)?",parent=self):return
        errors=[]
        for p in selected:
            try:
                args=["clean","-fd"]+(["-x"] if self.include_ignored.get() else [])+["--",p];git(self.repo,*args)
            except Exception as e:errors.append(f"{p}: {e}")
        messagebox.showinfo("Selective clean","Completed." if not errors else "Completed with errors:\n"+"\n".join(errors),parent=self);self.refresh()

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
            stat=git(self.repo,"show","--stat","--find-renames",r[0],"--",p);content=subprocess.run(["git","show",f"{r[0]}:{p}"],cwd=self.repo,capture_output=True,timeout=120)
            body=content.stdout.decode("utf-8",errors="replace") if content.returncode==0 and b"\x00" not in content.stdout[:8192] else "(Historical path unavailable at this commit, renamed, deleted, or binary.)"
            v=stat+"\n\nHISTORICAL CONTENT\n"+"="*72+"\n"+body
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        r=self.selected();p=self.path.get().strip()
        if not r:return
        dest=filedialog.asksaveasfilename(parent=self,initialfile=Path(p).name)
        if dest:
            out=subprocess.run(["git","show",f"{r[0]}:{p}"],cwd=self.repo,capture_output=True,timeout=120)
            if out.returncode:messagebox.showerror("Export",out.stderr.decode("utf-8",errors="replace"),parent=self)
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
            r=subprocess.run(["git","ls-remote",self.remote.get().strip()],cwd=self.repo,env=env,text=True,capture_output=True,timeout=120,encoding="utf-8",errors="replace");self.show((r.stdout+"\n"+r.stderr).strip())
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
        gd=self.gitdir();alt=gd/"objects"/"info"/"alternates";alternates=alt.read_text(encoding="utf-8",errors="replace") if alt.exists() else "None"
        env=os.environ.get("GIT_ALTERNATE_OBJECT_DIRECTORIES","Not set");objects=git(self.repo,"count-objects","-vH");self.report=f"OBJECT ALTERNATES\n{'='*72}\nGit dir: {gd}\nAlternates file: {alt}\n\nConfigured alternates:\n{alternates}\n\nEnvironment alternates:\n{env}\n\nLOCAL OBJECT STATUS\n{objects}"
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="object-alternates.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")
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
        p=Path(self.repo)/".gitattributes";v+=p.read_text(encoding="utf-8",errors="replace") if p.exists() else "Missing .gitattributes"
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
        if p:Path(p).write_text(self.report,encoding="utf-8")

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
        if p:Path(p).write_text(self.manifest,encoding="utf-8")
    def verify(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Manifest","*.txt"),("All files","*")])
        if not p:return
        expected={}
        for line in Path(p).read_text(encoding="utf-8",errors="replace").splitlines():
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
