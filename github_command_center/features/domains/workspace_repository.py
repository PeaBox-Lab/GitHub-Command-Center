"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

class WorktreeCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Worktree Center");self.geometry("900x620");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Add worktree",self.add),("Remove selected",self.remove),("Prune",self.prune)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("path","head","branch"),show="headings");
        for c,t,w in [("path","Path",450),("head","HEAD",120),("branch","Branch",220)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:
            raw=git(self.repo,"worktree","list","--porcelain");self.rows=[];cur={}
            for line in raw.splitlines()+[""]:
                if not line:
                    if cur:self.rows.append(cur);cur={}
                elif " " in line:
                    k,v=line.split(" ",1);cur[k]=v
            self.tree.delete(*self.tree.get_children())
            for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r.get("worktree",""),r.get("HEAD","")[:10],r.get("branch","").replace("refs/heads/","")))
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Worktrees",str(e),parent=self)
    def add(self):
        folder=filedialog.askdirectory(title="Choose parent folder for worktree",parent=self)
        if not folder:return
        branch=simpledialog.askstring("Worktree","Existing branch name, or new branch name:",parent=self)
        if not branch:return
        target=str(Path(folder)/branch.replace("/","-"))
        exists=git(self.repo,"branch","--list",branch)
        try:
            out=git(self.repo,"worktree","add",target,branch) if exists!="Completed successfully." else git(self.repo,"worktree","add","-b",branch,target)
            messagebox.showinfo("Worktree",out,parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Worktree",str(e),parent=self)
    def remove(self):
        s=self.tree.selection()
        if not s:return
        path=self.rows[int(s[0])].get("worktree","")
        if path==str(Path(self.repo).resolve()):return messagebox.showwarning("Worktree","The main worktree cannot be removed here.",parent=self)
        if messagebox.askyesno("Remove worktree",f"Remove worktree?\n{path}",parent=self):
            try:messagebox.showinfo("Worktree",git(self.repo,"worktree","remove",path),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Worktree",str(e),parent=self)
    def prune(self):
        try:messagebox.showinfo("Worktree",git(self.repo,"worktree","prune"),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Worktree",str(e),parent=self)

class RepositoryCompareCenter(tk.Toplevel):
    """Compare branches, tags or commits before merge/release and export a review report."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Compare & Review Center");self.geometry("1200x780");self.minsize(980,650);self._build();self.refresh_refs()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        ttk.Label(top,text="Base").pack(side="left");self.base=tk.StringVar();self.base_box=ttk.Combobox(top,textvariable=self.base,width=28);self.base_box.pack(side="left",padx=4)
        ttk.Label(top,text="Compare").pack(side="left",padx=(10,0));self.compare=tk.StringVar();self.compare_box=ttk.Combobox(top,textvariable=self.compare,width=28);self.compare_box.pack(side="left",padx=4)
        ttk.Button(top,text="Compare",command=self.run_compare).pack(side="left",padx=4);ttk.Button(top,text="Export report",command=self.export_report).pack(side="left")
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self.summary_tab=ttk.Frame(self.tabs,padding=8);self.files_tab=ttk.Frame(self.tabs,padding=8);self.commits_tab=ttk.Frame(self.tabs,padding=8);self.diff_tab=ttk.Frame(self.tabs,padding=8)
        for f,t in [(self.summary_tab,"Summary"),(self.files_tab,"Files"),(self.commits_tab,"Commits"),(self.diff_tab,"Unified diff")]:self.tabs.add(f,text=t)
        self.summary=tk.Text(self.summary_tab,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="both",expand=True)
        self.files=tk.Text(self.files_tab,wrap="none",font=("Consolas",9));self.files.pack(fill="both",expand=True)
        self.commits=tk.Text(self.commits_tab,wrap="none",font=("Consolas",9));self.commits.pack(fill="both",expand=True)
        self.diff=tk.Text(self.diff_tab,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.diff.pack(fill="both",expand=True)
        self.report=""
    def refresh_refs(self):
        try:
            raw=git(self.repo,"for-each-ref","--format=%(refname:short)","refs/heads/","refs/remotes/","refs/tags/")
            refs=[x for x in raw.splitlines() if x and x!="Completed successfully."]
            self.base_box["values"]=refs;self.compare_box["values"]=refs
            current=git(self.repo,"branch","--show-current")
            if refs:self.base.set("main" if "main" in refs else refs[0]);self.compare.set(current if current in refs else refs[min(1,len(refs)-1)])
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Compare",str(e),parent=self)
    def put(self,w,v):w.delete("1.0","end");w.insert("1.0",v)
    def run_compare(self):
        a=self.base.get().strip();b=self.compare.get().strip()
        if not a or not b:return
        try:
            ahead=git(self.repo,"rev-list","--count",f"{a}..{b}");behind=git(self.repo,"rev-list","--count",f"{b}..{a}")
            stat=git(self.repo,"diff","--stat",f"{a}...{b}");num=git(self.repo,"diff","--numstat",f"{a}...{b}");names=git(self.repo,"diff","--name-status",f"{a}...{b}")
            commits=git(self.repo,"log","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s",f"{a}..{b}")
            udiff=git(self.repo,"diff","--no-ext-diff",f"{a}...{b}")
            additions=deletions=files=0
            if num!="Completed successfully.":
                for line in num.splitlines():
                    p=line.split("\t")
                    if len(p)>=3:
                        files+=1
                        if p[0].isdigit():additions+=int(p[0])
                        if p[1].isdigit():deletions+=int(p[1])
            summary=f"COMPARE: {a} ... {b}\n"+"="*78+f"\nCommits only in compare: {ahead}\nCommits only in base   : {behind}\nChanged files          : {files}\nAdditions              : {additions}\nDeletions              : {deletions}\n\nDIFF STAT\n{stat}\n"
            self.put(self.summary,summary);self.put(self.files,names);self.put(self.commits,commits);self.put(self.diff,udiff)
            self.report=summary+"\nFILES\n"+names+"\n\nCOMMITS\n"+commits+"\n\nDIFF\n"+udiff
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Compare",str(e),parent=self)
    def export_report(self):
        if not self.report:self.run_compare()
        if not self.report:return
        path=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-comparison.txt")
        if path:Path(path).write_text(self.report,encoding="utf-8");messagebox.showinfo("Export",f"Saved {path}",parent=self)

class BackupRestoreCenter(tk.Toplevel):
    """Local recovery checkpoints using refs, stashes and bundles."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Backup & Recovery Center");self.geometry("1050x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Create checkpoint",self.checkpoint),("Create full bundle",self.bundle),("Verify bundle",self.verify),("Restore bundle to folder",self.restore_bundle)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:
            refs=git(self.repo,"for-each-ref","--sort=-creatordate","--format=%(creatordate:short)%09%(refname:short)%09%(objectname:short)%09%(subject)","refs/heads/gccc-backup/")
            st=git(self.repo,"stash","list")
            txt="SAFETY CHECKPOINT BRANCHES\n"+"="*72+"\n"+(refs if refs!="Completed successfully." else "None")+"\n\nSTASHES\n"+"="*72+"\n"+(st if st!="Completed successfully." else "None")
            self.text.delete("1.0","end");self.text.insert("1.0",txt)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Recovery",str(e),parent=self)
    def checkpoint(self):
        import datetime
        label=simpledialog.askstring("Checkpoint","Optional label:",initialvalue="manual",parent=self) or "manual"
        safe="".join(c if c.isalnum() or c in "-_" else "-" for c in label)
        name=f"gccc-backup/{safe}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:messagebox.showinfo("Checkpoint",git(self.repo,"branch",name),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Checkpoint",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=Path(self.repo).name+"-backup.bundle")
        if p:
            try:messagebox.showinfo("Bundle",git(self.repo,"bundle","create",p,"--all"),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Bundle",str(e),parent=self)
    def verify(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle"),("All files","*")])
        if p:
            try:messagebox.showinfo("Bundle verification",git(self.repo,"bundle","verify",p),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Bundle verification",str(e),parent=self)
    def restore_bundle(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle")])
        if not p:return
        parent=filedialog.askdirectory(parent=self,title="Choose folder in which to restore the repository")
        if not parent:return
        name=simpledialog.askstring("Restore","New repository folder name:",initialvalue=Path(self.repo).name+"-recovered",parent=self)
        if name:
            try:messagebox.showinfo("Restore",git(parent,"clone",p,name),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Restore",str(e),parent=self)

class RepositoryManager(tk.Toplevel):
    """Multi-repository command center for local portfolios."""
    def __init__(self,parent,start_repo=""):
        super().__init__(parent);self.title("Repository Manager");self.geometry("1200x760");self.minsize(980,650)
        self.workspace=Path(start_repo).parent if start_repo else Path.home()/"GitHub";self.rows=[];self._build();self.scan()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.workspace));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Browse",command=self.browse).pack(side="left",padx=3);ttk.Button(top,text="Scan",command=self.scan).pack(side="left");ttk.Button(top,text="Fetch selected",command=self.fetch).pack(side="left",padx=3);ttk.Button(top,text="Open Local Git",command=self.open_local).pack(side="left")
        cols=("repo","branch","state","ahead","behind","remote")
        self.tree=ttk.Treeview(self,columns=cols,show="headings",selectmode="extended")
        for c,t,w in [("repo","Repository",260),("branch","Branch",130),("state","Working tree",110),("ahead","Ahead",70),("behind","Behind",70),("remote","Origin",420)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<Double-1>",lambda e:self.open_local())
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.path.set(p);self.scan()
    def scan(self):
        root=Path(self.path.get());self.rows=[];self.tree.delete(*self.tree.get_children())
        if not root.exists():return
        candidates=[]
        if (root/".git").exists():candidates=[root]
        else:
            for p in root.iterdir():
                if p.is_dir() and (p/".git").exists():candidates.append(p)
        for p in sorted(candidates):
            try:
                branch=git(p,"branch","--show-current");status=git(p,"status","--porcelain");state="Clean" if status=="Completed successfully." else "Changed"
                try:remote=git(p,"remote","get-url","origin")
                except HANDLED_EXCEPTIONS:remote="-"
                try:ahead=git(p,"rev-list","--count","@{u}..HEAD");behind=git(p,"rev-list","--count","HEAD..@{u}")
                except HANDLED_EXCEPTIONS:ahead=behind="-"
                row={"path":str(p),"branch":branch,"state":state,"ahead":ahead,"behind":behind,"remote":remote};self.rows.append(row)
                self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p.name,branch,state,ahead,behind,remote))
            except HANDLED_EXCEPTIONS:pass
    def selected(self):return [self.rows[int(i)] for i in self.tree.selection()]
    def fetch(self):
        selected=self.selected()
        if not selected:return
        errors=[]
        for r in selected:
            try:git(r["path"],"fetch","--all","--prune")
            except HANDLED_EXCEPTIONS as e:errors.append(f"{Path(r['path']).name}: {e}")
        self.scan();messagebox.showinfo("Fetch", "Completed." if not errors else "Completed with errors:\n"+"\n".join(errors),parent=self)
    def open_local(self):
        s=self.selected()
        if s:LocalGitWindow(self,s[0]["path"])

class SettingsDiagnosticsCenter(tk.Toplevel):
    """1.0 diagnostics for required tools and repository configuration."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Diagnostics & Configuration");self.geometry("1000x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Run diagnostics",command=self.refresh).pack(side="left");ttk.Button(top,text="Copy report",command=self.copy).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def cmdver(self,cmd,args):
        try:
            r=subprocess.run([cmd,*args],text=True,capture_output=True,timeout=20,encoding="utf-8",errors="replace")
            return (r.returncode==0,(r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else "Available")
        except HANDLED_EXCEPTIONS as e:return False,str(e)
    def refresh(self):
        lines=["GITHUB COMMAND CENTER 1.0 DIAGNOSTICS","="*78]
        import sys,platform
        lines += [f"Python: {sys.version.split()[0]}",f"OS: {platform.platform()}",f"Repository: {self.repo}"]
        for name,cmd,args in [("Git","git",["--version"]),("GitHub CLI","gh",["--version"]),("pip-audit","pip-audit",["--version"]),("Bandit","bandit",["--version"])]:
            ok,v=self.cmdver(cmd,args);lines.append(f"{'PASS' if ok else 'WARN':4} {name}: {v}")
        try:
            lines.append("\nGit config")
            for key in ("user.name","user.email","core.autocrlf","pull.rebase"):
                try:v=git(self.repo,"config","--get",key)
                except HANDLED_EXCEPTIONS:v="Not set"
                lines.append(f"  {key}: {v}")
            lines.append("\nRepository integrity\n  "+git(self.repo,"fsck","--no-progress").replace("\n","\n  "))
        except HANDLED_EXCEPTIONS as e:lines.append("Repository diagnostics error: "+str(e))
        self.report="\n".join(lines);self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def copy(self):self.clipboard_clear();self.clipboard_append(getattr(self,"report",""));messagebox.showinfo("Diagnostics","Report copied to clipboard.",parent=self)

class SearchCenter(tk.Toplevel):
    """Search commits, tracked files and repository text from one UI."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Search Center");self.geometry("1100x720");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.q=tk.StringVar();ttk.Entry(top,textvariable=self.q).pack(side="left",fill="x",expand=True)
        for t,c in [("Search text",self.search_text),("Search commits",self.search_commits),("Search files",self.search_files)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def put(self,title,value):self.out.delete("1.0","end");self.out.insert("1.0",title+"\n"+"="*72+"\n\n"+value)
    def search_text(self):
        q=self.q.get().strip()
        if not q:return
        try:self.put("TRACKED TEXT SEARCH",git(self.repo,"grep","-n","-I","--",q))
        except HANDLED_EXCEPTIONS as e:self.put("TRACKED TEXT SEARCH",str(e))
    def search_commits(self):
        q=self.q.get().strip()
        if not q:return
        try:self.put("COMMIT MESSAGE SEARCH",git(self.repo,"log","--all","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s","--grep",q,"-i"))
        except HANDLED_EXCEPTIONS as e:self.put("COMMIT MESSAGE SEARCH",str(e))
    def search_files(self):
        q=self.q.get().strip().lower()
        if not q:return
        try:
            files=git(self.repo,"ls-files");matches=[x for x in files.splitlines() if q in x.lower()];self.put("FILE NAME SEARCH","\n".join(matches) if matches else "No tracked filenames matched.")
        except HANDLED_EXCEPTIONS as e:self.put("FILE NAME SEARCH",str(e))
