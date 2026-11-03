"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

class PluginManager(tk.Toplevel):
    """Manage local JSON command plugins without importing arbitrary Python modules."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.dir=Path(repo)/".git"/"gccc-plugins";self.title("Plugin Manager");self.geometry("1080x720");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.load),("Create plugin",self.create),("Run selected",self.run),("Enable/disable",self.toggle),("Delete",self.delete),("Open plugin folder",self.open_folder)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Segoe UI",10));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.describe())
        self.out=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="Plugins are JSON command definitions stored under .git/gccc-plugins. Commands run directly without a shell. Review every plugin before execution.",padding=8).pack(fill="x")
    def load(self):
        import json
        self.dir.mkdir(parents=True,exist_ok=True);self.plugins=[]
        for p in sorted(self.dir.glob("*.json")):
            try:
                d=json.loads(p.read_text(encoding="utf-8"));d["_path"]=p;self.plugins.append(d)
            except HANDLED_EXCEPTIONS:pass
        self.list.delete(0,"end")
        for p in self.plugins:self.list.insert("end",("[ON] " if p.get("enabled",True) else "[OFF] ")+p.get("name",p["_path"].stem))
    def selected(self):
        s=self.list.curselection();return self.plugins[s[0]] if s else None
    def describe(self):
        import json
        p=self.selected()
        if p:self.out.delete("1.0","end");self.out.insert("1.0",json.dumps({k:v for k,v in p.items() if k!="_path"},indent=2))
    def create(self):
        import json,re,shlex
        name=simpledialog.askstring("Plugin","Display name:",parent=self);cmd=simpledialog.askstring("Plugin","Command line:",parent=self) if name else None
        if not cmd:return
        slug=re.sub(r"[^a-z0-9_-]+","-",name.lower()).strip("-") or "plugin"
        d={"name":name,"description":"Local command plugin","command":shlex.split(cmd),"enabled":True}
        (self.dir/f"{slug}.json").write_text(json.dumps(d,indent=2),encoding="utf-8");self.load()
    def run(self):
        p=self.selected()
        if not p or not p.get("enabled",True):return
        command=p.get("command")
        if not isinstance(command,list) or not command:return messagebox.showerror("Plugin","Plugin command must be a JSON array.",parent=self)
        if not messagebox.askyesno("Run plugin",f"Run {p.get('name')}?\n\n{' '.join(command)}",parent=self):return
        try:r=subprocess.run(command,cwd=self.repo,text=True,capture_output=True,timeout=1800,encoding="utf-8",errors="replace");v=f"Exit code: {r.returncode}\n\n{r.stdout}\n{r.stderr}"
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def toggle(self):
        import json
        p=self.selected()
        if p:p["enabled"]=not p.get("enabled",True);p["_path"].write_text(json.dumps({k:v for k,v in p.items() if k!="_path"},indent=2),encoding="utf-8");self.load()
    def delete(self):
        p=self.selected()
        if p and messagebox.askyesno("Delete plugin",f"Delete {p.get('name')}?",parent=self):p["_path"].unlink();self.load()
    def open_folder(self):
        import os
        os.startfile(self.dir) if hasattr(os,"startfile") else subprocess.Popen(["xdg-open",str(self.dir)])

class BatchOperationsCenter(tk.Toplevel):
    """Portfolio operations with dry-run and per-repository results."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.root=Path(repo).parent;self.title("Batch Operations Center");self.geometry("1180x760");self._build();self.scan()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.root));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Button(top,text="Browse",command=self.browse).pack(side="left",padx=3);ttk.Button(top,text="Scan",command=self.scan).pack(side="left")
        self.op=tk.StringVar(value="Fetch/prune");ttk.Combobox(top,textvariable=self.op,values=["Fetch/prune","Status","Integrity check","Python compile","Pull FF-only"],state="readonly",width=18).pack(side="left",padx=5);ttk.Button(top,text="Run selected",command=self.run).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("repo","branch","state","result"),show="headings",selectmode="extended")
        for c,t,w in [("repo","Repository",260),("branch","Branch",160),("state","State",100),("result","Last result",520)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Pull FF-only is skipped for repositories with local changes. Batch operations run sequentially and never force changes.",padding=8).pack(fill="x")
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.path.set(p);self.scan()
    def scan(self):
        root=Path(self.path.get());self.rows=[];self.tree.delete(*self.tree.get_children())
        if not root.exists():return
        candidates=[root] if (root/".git").exists() else [p for p in root.iterdir() if p.is_dir() and (p/".git").exists()]
        for p in sorted(candidates):
            try:b=git(p,"branch","--show-current");s=git(p,"status","--porcelain");state="Clean" if s=="Completed successfully." else "Changed";self.rows.append({"path":p,"branch":b,"state":state,"result":""});self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p.name,b,state,""))
            except HANDLED_EXCEPTIONS:pass
    def run(self):
        ids=self.tree.selection()
        if not ids:return
        op=self.op.get()
        if not messagebox.askyesno("Batch operation",f"Run '{op}' on {len(ids)} selected repositories?",parent=self):return
        for iid in ids:
            r=self.rows[int(iid)];p=r["path"]
            try:
                if op=="Fetch/prune":out=git(p,"fetch","--all","--prune")
                elif op=="Status":out=git(p,"status","--short","--branch")
                elif op=="Integrity check":out=git(p,"fsck","--no-progress")
                elif op=="Python compile":
                    x=subprocess.run(["python","-m","compileall","-q","."],cwd=p,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace");out=f"Exit {x.returncode}: {(x.stdout+x.stderr).strip()}"
                elif r["state"]!="Clean":out="SKIPPED: local changes"
                else:out=git(p,"pull","--ff-only")
            except HANDLED_EXCEPTIONS as e:out="ERROR: "+str(e)
            short=out.replace("\n"," | ")[:500];self.tree.set(iid,"result",short)

class RepositoryDashboardCenter(tk.Toplevel):
    """One-page operational dashboard for the selected repository."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Operations Dashboard");self.geometry("1150x760");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Smart Sync",command=lambda:SyncCenter(self,self.repo)).pack(side="left",padx=3);ttk.Button(top,text="Review",command=lambda:ChangeReviewCenter(self,self.repo)).pack(side="left");ttk.Button(top,text="Release policy",command=lambda:ReleasePolicyCenter(self,self.repo)).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except HANDLED_EXCEPTIONS as e:return "Unavailable: "+str(e)
    def refresh(self):
        branch=self.safe("branch","--show-current");status=self.safe("status","--porcelain");clean=status=="Completed successfully."
        try:up=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");ahead=self.safe("rev-list","--count","@{u}..HEAD");behind=self.safe("rev-list","--count","HEAD..@{u}")
        except HANDLED_EXCEPTIONS:up=ahead=behind="-"
        last=self.safe("log","-1","--date=short","--pretty=format:%h %ad %an %s");tags=self.safe("tag","--sort=-creatordate").splitlines()[:5];changes=0 if clean else len(status.splitlines())
        health=[]
        for f in ("README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md"):health.append((f,(Path(self.repo)/f).exists()))
        report=f"REPOSITORY OPERATIONS DASHBOARD\n{'='*78}\nRepository: {self.repo}\nBranch: {branch}\nUpstream: {up}\nAhead / Behind: {ahead} / {behind}\nWorking tree: {'Clean' if clean else f'{changes} changed entries'}\nLast commit: {last}\n\nRECENT TAGS\n"+"\n".join(tags or ["None"])+"\n\nDOCUMENTATION CONTROLS\n"+"\n".join(f"[{'PASS' if ok else 'MISS'}] {f}" for f,ok in health)+"\n\nRECOMMENDED NEXT ACTION\n"
        if not clean:report+="Review and commit or stash local changes."
        elif str(behind)!="0" and str(ahead)=="0":report+="Run Smart Sync to fast-forward from upstream."
        elif str(ahead)!="0" and str(behind)=="0":report+="Review and push local commits."
        elif str(ahead)!="0" and str(behind)!="0":report+="Histories diverged. Use Compare before merge or rebase."
        else:report+="Repository is synchronized and clean."
        self.text.delete("1.0","end");self.text.insert("1.0",report)

class DataExportCenter(tk.Toplevel):
    """Export local repository metadata in JSON or CSV for analysis."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Data Export");self.geometry("1000x680");self._build();self.preview()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Preview",self.preview),("Export JSON",self.json_export),("Export commits CSV",self.csv_export)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def collect(self):
        import json
        def safe(*a):
            try:return git(self.repo,*a)
            except HANDLED_EXCEPTIONS:return ""
        commits=[]
        raw=safe("log","-500","--date=iso-strict","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%ae%x1f%s")
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:commits.append(dict(hash=p[0],short=p[1],date=p[2],author=p[3],email=p[4],subject=p[5]))
        return {"repository":Path(self.repo).name,"path":self.repo,"branch":safe("branch","--show-current"),"remotes":safe("remote","-v").splitlines(),"tags":safe("tag","--sort=-creatordate").splitlines(),"commits":commits}
    def preview(self):
        import json
        self.data=self.collect();self.text.delete("1.0","end");self.text.insert("1.0",json.dumps({**self.data,"commits":self.data["commits"][:10]},indent=2)+"\n\nPreview shows the latest 10 of up to 500 exported commits.")
    def json_export(self):
        import json
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile=Path(self.repo).name+"-repository-data.json")
        if p:Path(p).write_text(json.dumps(self.collect(),indent=2),encoding="utf-8")
    def csv_export(self):
        import csv
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",initialfile=Path(self.repo).name+"-commits.csv")
        if p:
            with open(p,"w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["hash","short","date","author","email","subject"]);w.writeheader();w.writerows(self.collect()["commits"])

class BackgroundJobsCenter(tk.Toplevel):
    """Run long commands in background threads with queue, logs and cancellation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Background Jobs Center");self.geometry("1120x740");self.jobs=[];self.processes={};self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.command=tk.StringVar(value="git fetch --all --prune");ttk.Entry(top,textvariable=self.command).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Queue command",command=self.queue).pack(side="left",padx=3);ttk.Button(top,text="Cancel selected",command=self.cancel).pack(side="left");ttk.Button(top,text="Clear finished",command=self.clear).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.tree=ttk.Treeview(a,columns=("id","command","status","code"),show="headings")
        for c,t,w in [("id","ID",60),("command","Command",650),("status","Status",130),("code","Exit",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.show_log())
        self.log=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.log.pack(fill="both",expand=True)
        ttk.Label(self,text="Commands are parsed into argument arrays and run without a shell. Cancellation terminates the local process.",padding=8).pack(fill="x")
    def queue(self):
        import shlex,threading,time
        try:args=shlex.split(self.command.get())
        except HANDLED_EXCEPTIONS as e:return messagebox.showerror("Job",str(e),parent=self)
        if not args:return
        job={"id":len(self.jobs)+1,"args":args,"status":"Queued","code":"","log":""};self.jobs.append(job);iid=str(job["id"]);self.tree.insert("","end",iid=iid,values=(job["id"]," ".join(args),job["status"],""))
        def worker():
            job["status"]="Running";self.after(0,lambda:self.update_row(job))
            try:
                p=subprocess.Popen(args,cwd=self.repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding="utf-8",errors="replace");self.processes[job["id"]]=p
                for line in iter(p.stdout.readline,""):
                    job["log"]+=line
                    self.after(0,self.show_log)
                p.wait();job["code"]=p.returncode;job["status"]="Completed" if p.returncode==0 else "Failed"
            except HANDLED_EXCEPTIONS as e:job["log"]+=str(e);job["status"]="Failed";job["code"]="-"
            self.processes.pop(job["id"],None);self.after(0,lambda:self.update_row(job))
        threading.Thread(target=worker,daemon=True).start()
    def update_row(self,j):self.tree.item(str(j["id"]),values=(j["id"]," ".join(j["args"]),j["status"],j["code"]))
    def current(self):
        s=self.tree.selection();return next((j for j in self.jobs if str(j["id"])==s[0]),None) if s else None
    def show_log(self):
        j=self.current()
        if j:self.log.delete("1.0","end");self.log.insert("1.0",j["log"] or "No output yet.")
    def cancel(self):
        j=self.current();p=self.processes.get(j["id"]) if j else None
        if p and messagebox.askyesno("Cancel job",f"Terminate job {j['id']}?",parent=self):p.terminate();j["status"]="Cancelled";self.update_row(j)
    def clear(self):
        keep=[j for j in self.jobs if j["status"] in ("Queued","Running")];self.jobs=keep;self.tree.delete(*self.tree.get_children())
        for j in keep:self.tree.insert("","end",iid=str(j["id"]),values=(j["id"]," ".join(j["args"]),j["status"],j["code"]))

class PreferencesCenter(tk.Toplevel):
    """Persist local application preferences and UI defaults."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path.home()/".gccc-preferences.json";self.title("Preferences & Appearance");self.geometry("760x540");self._build();self.load()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.theme=tk.StringVar(value="clam");self.font=tk.IntVar(value=9);self.limit=tk.IntVar(value=200);self.confirm=tk.BooleanVar(value=True);self.default_branch=tk.StringVar(value="main")
        rows=[("Tk theme",ttk.Combobox(f,textvariable=self.theme,values=ttk.Style().theme_names(),state="readonly")),("Editor font size",ttk.Spinbox(f,from_=8,to=18,textvariable=self.font)),("History row limit",ttk.Spinbox(f,from_=50,to=2000,increment=50,textvariable=self.limit)),("Default base branch",ttk.Entry(f,textvariable=self.default_branch))]
        for i,(label,w) in enumerate(rows):ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=8);w.grid(row=i,column=1,sticky="ew",padx=8,pady=8)
        ttk.Checkbutton(f,text="Require confirmation for destructive operations",variable=self.confirm).grid(row=4,column=1,sticky="w",pady=8);f.columnconfigure(1,weight=1)
        ttk.Button(f,text="Save preferences",command=self.save).grid(row=5,column=1,sticky="e",pady=18)
        ttk.Label(f,text="Theme changes apply immediately. Other values are defaults for future modular centers and are stored outside repositories.",wraplength=620).grid(row=6,column=0,columnspan=2,sticky="w")
    def load(self):
        import json
        if self.path.exists():
            try:
                p=json.loads(self.path.read_text(encoding="utf-8"));self.theme.set(p.get("theme","clam"));self.font.set(p.get("font_size",9));self.limit.set(p.get("history_limit",200));self.confirm.set(p.get("confirm_destructive",True));self.default_branch.set(p.get("default_branch","main"))
            except HANDLED_EXCEPTIONS:pass
    def save(self):
        import json
        p={"theme":self.theme.get(),"font_size":self.font.get(),"history_limit":self.limit.get(),"confirm_destructive":self.confirm.get(),"default_branch":self.default_branch.get()};self.path.write_text(json.dumps(p,indent=2),encoding="utf-8")
        try:ttk.Style().theme_use(self.theme.get())
        except HANDLED_EXCEPTIONS:pass
        messagebox.showinfo("Preferences",f"Saved {self.path}",parent=self)

class PortfolioHistoryCenter(tk.Toplevel):
    """SQLite-backed snapshots of local repository portfolio state."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.root=Path(repo).parent;self.db=Path.home()/".gccc-portfolio.sqlite3";self.title("Portfolio History");self.geometry("1180x740");self._build();self.init_db();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.root));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Button(top,text="Capture snapshot",command=self.capture).pack(side="left",padx=3);ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export CSV",command=self.export).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("time","repo","branch","state","ahead","behind"),show="headings")
        for c,t,w in [("time","Captured",170),("repo","Repository",280),("branch","Branch",150),("state","State",90),("ahead","Ahead",70),("behind","Behind",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def init_db(self):
        import sqlite3
        with sqlite3.connect(self.db) as c:c.execute("create table if not exists snapshots(captured text, path text, repo text, branch text, state text, ahead text, behind text)")
    def capture(self):
        import sqlite3,datetime
        root=Path(self.path.get());repos=[root] if (root/".git").exists() else [p for p in root.iterdir() if p.is_dir() and (p/".git").exists()]
        rows=[];now=datetime.datetime.now().isoformat(timespec="seconds")
        for p in repos:
            try:
                branch=git(p,"branch","--show-current");s=git(p,"status","--porcelain");state="Clean" if s=="Completed successfully." else "Changed"
                try:a=git(p,"rev-list","--count","@{u}..HEAD");b=git(p,"rev-list","--count","HEAD..@{u}")
                except HANDLED_EXCEPTIONS:a=b="-"
                rows.append((now,str(p),p.name,branch,state,a,b))
            except HANDLED_EXCEPTIONS:pass
        with sqlite3.connect(self.db) as c:c.executemany("insert into snapshots values(?,?,?,?,?,?,?)",rows)
        self.refresh();messagebox.showinfo("Portfolio",f"Captured {len(rows)} repositories.",parent=self)
    def refresh(self):
        import sqlite3
        self.tree.delete(*self.tree.get_children())
        with sqlite3.connect(self.db) as c:rows=c.execute("select captured,repo,branch,state,ahead,behind from snapshots order by captured desc limit 1000").fetchall()
        for r in rows:self.tree.insert("","end",values=r)
    def export(self):
        import sqlite3,csv
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",initialfile="portfolio-history.csv")
        if not p:return
        with sqlite3.connect(self.db) as c:rows=c.execute("select captured,path,repo,branch,state,ahead,behind from snapshots order by captured").fetchall()
        with open(p,"w",newline="",encoding="utf-8") as f:w=csv.writer(f);w.writerow(["captured","path","repo","branch","state","ahead","behind"]);w.writerows(rows)
