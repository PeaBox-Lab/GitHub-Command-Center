"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.process_gateway import run_process, start_process
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

class RepositoryLocatorCenter(tk.Toplevel):
    """Scan a workspace recursively for Git repositories and open them quickly."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.root=Path(repo).parent;self.title("Repository Locator");self.geometry("1120x720");self.rows=[];self._build();self.scan()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.path=tk.StringVar(value=str(self.root));self.depth=tk.IntVar(value=3);ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Spinbox(bar,from_=1,to=8,textvariable=self.depth,width=5).pack(side="left",padx=4);ttk.Button(bar,text="Browse",command=self.browse).pack(side="left");ttk.Button(bar,text="Scan",command=self.scan).pack(side="left",padx=3);ttk.Button(bar,text="Open selected",command=self.open).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("name","path","branch","state"),show="headings")
        for c,t,w in [("name","Repository",240),("path","Path",560),("branch","Branch",160),("state","State",100)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<Double-1>",lambda e:self.open())
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.path.set(p);self.scan()
    def scan(self):
        root=Path(self.path.get());maxdepth=int(self.depth.get());self.rows=[];self.tree.delete(*self.tree.get_children())
        if not root.exists():return
        for gitdir in root.rglob(".git"):
            try:
                rel=gitdir.parent.relative_to(root)
                if len(rel.parts)>maxdepth:continue
                repo=gitdir.parent;branch=git(repo,"branch","--show-current");st=git(repo,"status","--porcelain");state="Clean" if st=="Completed successfully." else "Changed";r=(repo.name,str(repo),branch,state);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=r)
            except HANDLED_EXCEPTIONS:pass
    def open(self):
        s=self.tree.selection()
        if s:LocalGitWindow(self,self.rows[int(s[0])][1])

class BlameExplorerCenter(tk.Toplevel):
    """Line-oriented blame UI with commit inspection and file-history handoff."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Blame Explorer");self.geometry("1280x780");self.rows=[];self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.path=tk.StringVar();self.ref=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Entry(bar,textvariable=self.ref,width=18).pack(side="left",padx=4);ttk.Button(bar,text="Load blame",command=self.load).pack(side="left");ttk.Button(bar,text="Inspect commit",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Open file history",command=lambda:CommitInspector(self,self.repo)).pack(side="left")
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("line","hash","author","date","content"),show="headings")
        for c,t,w in [("line","Line",60),("hash","Commit",90),("author","Author",170),("date","Date",110),("content","Content",720)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def load(self):
        p=self.path.get().strip();ref=self.ref.get().strip() or "HEAD"
        if not p:return
        try:raw=git(self.repo,"blame","--line-porcelain",ref,"--",p)
        except HANDLED_EXCEPTIONS as e:return messagebox.showerror("Blame",str(e),parent=self)
        self.rows=[];self.tree.delete(*self.tree.get_children());cur={}
        for line in raw.splitlines():
            if line.startswith("\t"):
                cur["content"]=line[1:];self.rows.append(cur);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(cur.get("final",""),cur.get("hash","")[:10],cur.get("author",""),cur.get("date",""),cur.get("content","")));cur={}
            elif not cur and " " in line:
                x=line.split();cur={"hash":x[0],"final":x[2] if len(x)>2 else ""}
            elif line.startswith("author "):cur["author"]=line[7:]
            elif line.startswith("author-time "):
                import datetime
                try:cur["date"]=datetime.datetime.fromtimestamp(int(line.split()[1])).date().isoformat()
                except HANDLED_EXCEPTIONS:cur["date"]=""
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--patch","--find-renames",r["hash"])
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class CommitObjectCenter(tk.Toplevel):
    """Low-level object inspector for commits, trees, blobs and tags."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Object Inspector");self.geometry("1100x720");self._build()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.obj=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.obj).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Inspect",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="List tree",command=self.tree).pack(side="left");ttk.Button(bar,text="Verify object",command=self.verify).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Read-only plumbing view using cat-file, ls-tree and rev-parse. No object mutation is performed.",padding=8).pack(fill="x")
    def show(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def inspect(self):
        o=self.obj.get().strip()
        if not o:return
        try:
            sha=git(self.repo,"rev-parse",o);typ=git(self.repo,"cat-file","-t",sha);size=git(self.repo,"cat-file","-s",sha);content=git(self.repo,"cat-file","-p",sha);self.show(f"Object: {sha}\nType: {typ}\nSize: {size}\n\n{content}")
        except HANDLED_EXCEPTIONS as e:self.show(str(e))
    def tree(self):
        o=self.obj.get().strip() or "HEAD"
        try:self.show(git(self.repo,"ls-tree","-r","-l",o))
        except HANDLED_EXCEPTIONS as e:self.show(str(e))
    def verify(self):
        o=self.obj.get().strip()
        try:self.show(git(self.repo,"rev-parse","--verify",o))
        except HANDLED_EXCEPTIONS as e:self.show(str(e))

class BisectAutomationCenter(tk.Toplevel):
    """Automate regression hunting with git bisect run while keeping reset controls visible."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Automated Bisect Center");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.good=tk.StringVar();self.bad=tk.StringVar(value="HEAD");self.cmd=tk.StringVar(value="python -m pytest -q")
        ttk.Entry(bar,textvariable=self.good,width=18).pack(side="left");ttk.Entry(bar,textvariable=self.bad,width=18).pack(side="left",padx=3);ttk.Entry(bar,textvariable=self.cmd).pack(side="left",fill="x",expand=True,padx=3)
        for t,c in [("Start + run",self.run),("Reset bisect",self.reset),("Refresh",self.refresh)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The test command is parsed into an argument array. Exit 0 means good; 1-127 means bad except 125, which Git treats as skip.",padding=8).pack(fill="x")
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def refresh(self):
        try:v=git(self.repo,"status","--short","--branch")+"\n\n"+git(self.repo,"bisect","log")
        except HANDLED_EXCEPTIONS as e:v="No active bisect session or log unavailable.\n\n"+str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def run(self):
        import shlex
        if not self.clean():return messagebox.showwarning("Bisect","Commit or stash changes before automated bisect.",parent=self)
        good=self.good.get().strip();bad=self.bad.get().strip();cmd=shlex.split(self.cmd.get())
        if not good or not bad or not cmd:return messagebox.showwarning("Bisect","Enter known-good, known-bad and a test command.",parent=self)
        try:
            git(self.repo,"rev-parse","--verify",good);git(self.repo,"rev-parse","--verify",bad);git(self.repo,"bisect","start",bad,good)
            r=run_process(["git","bisect","run",*cmd],cwd=self.repo,text=True,capture_output=True,timeout=7200,encoding="utf-8",errors="replace");v=(r.stdout+"\n"+r.stderr).strip();self.out.delete("1.0","end");self.out.insert("1.0",v);messagebox.showinfo("Bisect",f"Automated bisect finished with exit code {r.returncode}. Review the output, then Reset bisect when done.",parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Bisect",str(e),parent=self)
    def reset(self):
        try:messagebox.showinfo("Bisect",git(self.repo,"bisect","reset"),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Bisect",str(e),parent=self)

class RevisionArchiveCenter(tk.Toplevel):
    """Export any revision or subdirectory without checking it out."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Revision Archive Center");self.geometry("900x600");self._build();self.preview()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.ref=tk.StringVar(value="HEAD");self.path=tk.StringVar();self.prefix=tk.BooleanVar(value=True)
        for i,(label,var) in enumerate((("Revision",self.ref),("Optional subdirectory",self.path))):ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=6);ttk.Entry(f,textvariable=var).grid(row=i,column=1,sticky="ew",padx=8,pady=6)
        ttk.Checkbutton(f,text="Prefix archive with repository-revision folder",variable=self.prefix).grid(row=2,column=1,sticky="w",pady=5);f.columnconfigure(1,weight=1)
        ttk.Button(f,text="Preview revision",command=self.preview).grid(row=3,column=0,pady=8);ttk.Button(f,text="Export ZIP",command=self.export,style="Accent.TButton").grid(row=3,column=1,sticky="e",pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=4,column=0,columnspan=2,sticky="nsew");f.rowconfigure(4,weight=1)
    def preview(self):
        try:v=git(self.repo,"show","-s","--date=iso-strict","--pretty=fuller",self.ref.get().strip() or "HEAD")
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        ref=self.ref.get().strip() or "HEAD";sub=self.path.get().strip().strip("/");name=Path(self.repo).name;safe=ref.replace("/","-").replace("\\","-");dest=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",initialfile=f"{name}-{safe}.zip")
        if not dest:return
        args=["archive","--format=zip",f"--output={dest}"]
        if self.prefix.get():args += [f"--prefix={name}-{safe}/"]
        args.append(ref)
        if sub:args.append(sub)
        try:messagebox.showinfo("Archive",git(self.repo,*args),parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Archive",str(e),parent=self)

class CommitMetadataCenter(tk.Toplevel):
    """Inspect author/committer identity, parents, signature and raw commit metadata."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Metadata Inspector");self.geometry("1120x720");self._build();self.inspect()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.ref=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.ref).pack(side="left",fill="x",expand=True);ttk.Button(bar,text="Inspect",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Copy metadata",command=self.copy).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def inspect(self):
        r=self.ref.get().strip() or "HEAD"
        try:
            self.report=git(self.repo,"show","-s","--show-signature","--date=iso-strict","--pretty=raw",r)+"\n\nFORMATTED\n"+git(self.repo,"show","-s","--date=iso-strict","--pretty=format:Commit: %H%nTree: %T%nParents: %P%nAuthor: %an <%ae>%nAuthor date: %aI%nCommitter: %cn <%ce>%nCommit date: %cI%nSignature status: %G?%nSigner: %GS%nKey: %GK%n%n%B",r)
        except HANDLED_EXCEPTIONS as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def copy(self):self.clipboard_clear();self.clipboard_append(getattr(self,"report",""));messagebox.showinfo("Metadata","Copied to clipboard.",parent=self)

class DanglingObjectRecoveryCenter(tk.Toplevel):
    """Inspect unreachable commits reported by git fsck and preserve them with branches."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Dangling Object Recovery");self.geometry("1200x760");self.rows=[];self._build();self.scan()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Scan",self.scan),("Inspect selected",self.inspect),("Create recovery branch",self.recover),("Export report",self.export)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("kind","object","date","subject"),show="headings")
        for c,t,w in [("kind","Kind",120),("object","Object",340),("date","Date",160),("subject","Subject / details",500)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.inspect())
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="Recovery is non-destructive: selected unreachable commits are preserved by creating a new local recovery branch. No objects are deleted.",padding=8).pack(fill="x")
    def scan(self):
        import re
        try:raw=git(self.repo,"fsck","--full","--no-reflogs","--unreachable")
        except HANDLED_EXCEPTIONS as e:raw=str(e)
        self.raw_report=raw;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            m=re.search(r"(?:unreachable|dangling) (commit|tree|blob|tag) ([0-9a-f]{40,64})",line)
            if not m:continue
            kind,sha=m.group(1),m.group(2);date=subject=""
            if kind=="commit":
                try:
                    info=git(self.repo,"show","-s","--date=iso-strict","--pretty=format:%cI%x1f%s",sha).split("\x1f",1);date=info[0];subject=info[1] if len(info)>1 else ""
                except HANDLED_EXCEPTIONS:pass
            else:subject=line
            self.rows.append(dict(kind=kind,sha=sha,date=date,subject=subject));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(kind,sha,date,subject))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"cat-file","-p",r["sha"]) if r["kind"]!="commit" else git(self.repo,"show","--stat","--patch","--find-renames",r["sha"])
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def recover(self):
        import datetime,re
        r=self.selected()
        if not r or r["kind"]!="commit":return messagebox.showinfo("Recovery","Select an unreachable commit. Trees and blobs cannot be branched directly.",parent=self)
        default=f"recovery/fsck-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{r['sha'][:8]}";name=simpledialog.askstring("Recovery branch","New branch name:",initialvalue=default,parent=self)
        if not name or not re.match(r"^[A-Za-z0-9._/-]+$",name):return
        try:messagebox.showinfo("Recovery",git(self.repo,"branch",name,r["sha"]),parent=self);self.scan()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Recovery",str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="dangling-object-report.txt")
        if p:Path(p).write_text(self.raw_report,encoding="utf-8")
