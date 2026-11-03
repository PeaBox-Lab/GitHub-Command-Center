"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.process_gateway import run_process, start_process
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

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
            except HANDLED_EXCEPTIONS as e:lines.append(str(e))
        self.out.delete("1.0","end");self.out.insert("1.0","\n\n".join(lines))
    def preview(self):
        r=self.selected()
        if not r:return
        m=int(self.mainline.get())
        if m<1 or m>len(r[4].split()):return messagebox.showwarning("Merge revert","Selected mainline parent does not exist.",parent=self)
        try:v=git(self.repo,"diff",f"{r[0]}^{m}",r[0],"--stat")+"\n\nREVERT WOULD INVERT THIS MERGE-SIDE CHANGE\n"+git(self.repo,"diff",f"{r[0]}^{m}",r[0],"--name-status")
        except HANDLED_EXCEPTIONS as e:v=str(e)
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
        except HANDLED_EXCEPTIONS as e:messagebox.showwarning("Merge revert",f"Revert paused or failed. Resolve conflicts and Continue, or Abort.\n\n{e}",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Revert",git(self.repo,"revert",arg),parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Revert",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:v=str(e)
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
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Git subtree",str(e),parent=self)
    def add(self):self.run("add",f"Add subtree at {self.prefix.get()} from {self.remote.get()} {self.ref.get()}?")
    def pull(self):self.run("pull",f"Pull subtree updates into {self.prefix.get()}?")
    def push(self):self.run("push",f"Push subtree {self.prefix.get()} to {self.remote.get()} {self.ref.get()}?")
    def split(self):
        branch=simpledialog.askstring("Subtree split","New local branch for split history:",parent=self)
        if branch:
            try:v=git(self.repo,"subtree","split",f"--prefix={self.prefix.get().strip()}",f"--branch={branch}");self.out.delete("1.0","end");self.out.insert("1.0",v)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Subtree split",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def check_tool(self):
        try:r=run_process(["git-filter-repo","--version"],text=True,capture_output=True,timeout=30,encoding="utf-8",errors="replace");v=(r.stdout+r.stderr).strip() or f"Exit {r.returncode}"
        except HANDLED_EXCEPTIONS as e:v="git-filter-repo not found. Install it from its official distribution before using generated commands.\n\n"+str(e)
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
            except HANDLED_EXCEPTIONS:continue
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
        except HANDLED_EXCEPTIONS as e:self.report=str(e)
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
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","CONFIGURED REFSPECS\n"+"="*72+"\n"+v)
    def preview_fetch(self):
        spec=f"{self.src.get().strip()}:{self.dst.get().strip()}"
        try:v=git(self.repo,"fetch","--dry-run",self.remote.get().strip(),spec)
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",f"FETCH DRY RUN\n{self.remote.get()} {spec}\n\n{v}")
    def preview_push(self):
        spec=f"{self.src.get().strip()}:{self.dst.get().strip()}"
        try:v=git(self.repo,"push","--dry-run",self.remote.get().strip(),spec)
        except HANDLED_EXCEPTIONS as e:v=str(e)
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
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","NOTES REFS\n"+"="*72+"\n"+v)
    def merge(self):
        local=self.local.get().strip();other=self.other.get().strip();strategy=self.strategy.get()
        if not local or not other:return
        if not messagebox.askyesno("Merge notes",f"Merge {other} into refs/notes/{local} using {strategy}?",parent=self):return
        try:messagebox.showinfo("Notes merge",git(self.repo,"notes",f"--ref={local}","merge",f"-s{strategy}",other),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Notes merge",str(e),parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Notes merge",git(self.repo,"notes",f"--ref={self.local.get().strip()}","merge",arg),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Notes merge",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:text=str(e)
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
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Merge",str(e),parent=self)
    def abort(self):
        try:messagebox.showinfo("Merge",git(self.repo,"merge","--abort"),parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Merge",str(e),parent=self)

class ConfigIncludeCenter(tk.Toplevel):
    """Inspect Git config include/includeIf rules and their resolved origins."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Config Include Inspector");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Open Git Configuration",command=lambda:GitConfigCenter(self,self.repo)).pack(side="left",padx=3);ttk.Button(bar,text="Export",command=self.export).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:incs=git(self.repo,"config","--show-origin","--show-scope","--get-regexp",r"^(include\.path|includeIf\..*\.path)$")
        except HANDLED_EXCEPTIONS as e:incs="No include rules found or Git returned:\n"+str(e)
        try:effective=git(self.repo,"config","--list","--show-origin","--show-scope","--includes")
        except HANDLED_EXCEPTIONS as e:effective=str(e)
        self.report="CONFIG INCLUDE RULES\n"+"="*72+"\n"+incs+"\n\nEFFECTIVE CONFIG WITH INCLUDES\n"+"="*72+"\n"+effective;self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="git-config-includes.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")
