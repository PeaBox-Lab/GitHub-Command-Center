import subprocess, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

class GitError(RuntimeError): pass

def git(cwd,*args):
    try:r=subprocess.run(["git",*args],cwd=cwd,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
    except FileNotFoundError:raise GitError("Git is not installed or not on PATH.")
    out=(r.stdout+"\n"+r.stderr).strip()
    if r.returncode:raise GitError(out or "Git command failed")
    return out or "Completed successfully."

class LocalGitWindow(tk.Toplevel):
    def __init__(self,parent,start=""):
        super().__init__(parent);self.title("Local Git Workspace");self.geometry("1250x760");self.minsize(1000,650)
        self.repo=start;self.sel=tk.StringVar(value=start or "No repository selected")
        top=ttk.Frame(self,padding=10);top.pack(fill="x");ttk.Label(top,textvariable=self.sel,font=("Segoe UI Semibold",11)).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Choose / Init",command=self.choose).pack(side="right",padx=3);ttk.Button(top,text="Clone",command=self.clone).pack(side="right",padx=3)
        bar=ttk.Frame(self,padding=(10,0));bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Stage selected",self.stage),("Stage all",lambda:self.run("add","--all")),("Unstage",self.unstage),("Commit",self.commit),("Fetch",lambda:self.run("fetch","--all","--prune")),("Pull FF-only",lambda:self.run("pull","--ff-only")),("Push",lambda:self.run("push"))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2,pady=5)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=10,pady=8)
        left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=3);pane.add(right,weight=2)
        self.files=ttk.Treeview(left,columns=("state","file"),show="headings",selectmode="extended");self.files.heading("state",text="State");self.files.heading("file",text="File");self.files.column("state",width=70);self.files.column("file",width=470);self.files.pack(fill="both",expand=True)
        foot=ttk.Frame(left);foot.pack(fill="x",pady=5)
        for t,c in [("Diff",self.diff),("Visual history",lambda:CommitGraphWindow(self,self.repo)),("Resolve conflicts",lambda:ConflictResolver(self,self.repo)),("Advanced",lambda:AdvancedGitWindow(self,self.repo)),("Release Center",lambda:ReleaseCenter(self,self.repo)),("Pull Requests",lambda:PullRequestCenter(self,self.repo)),("Actions",lambda:ActionsCenter(self,self.repo)),("Security",lambda:SecurityCenter(self,self.repo)),("Health",lambda:RepositoryHealthCenter(self,self.repo)),("Worktrees",lambda:WorktreeCenter(self,self.repo)),("Compare",lambda:RepositoryCompareCenter(self,self.repo)),("Recovery",lambda:BackupRestoreCenter(self,self.repo)),("Repo Manager",lambda:RepositoryManager(self,self.repo)),("Diagnostics",lambda:SettingsDiagnosticsCenter(self,self.repo)),("Smart Sync",lambda:SyncCenter(self,self.repo)),("Search",lambda:SearchCenter(self,self.repo)),("Review",lambda:ChangeReviewCenter(self,self.repo)),("Notes",lambda:RepositoryNotesCenter(self,self.repo)),("Cleanup",lambda:BranchCleanupCenter(self,self.repo)),("Snapshot",lambda:ProjectSnapshotCenter(self,self.repo)),("Patches",lambda:PatchCenter(self,self.repo)),("Bisect",lambda:BisectCenter(self,self.repo)),("Discard",self.discard),("Clean preview",self.clean),("Open folder",self.open_folder)]:ttk.Button(foot,text=t,command=c).pack(side="left",padx=2)
        self.tabs=ttk.Notebook(right);self.tabs.pack(fill="both",expand=True)
        self.texts={}
        for n in ["History","Branches","Stash","Tags","Remotes","Conflicts"]:
            f=ttk.Frame(self.tabs);self.tabs.add(f,text=n);b=ttk.Frame(f);b.pack(fill="x")
            if n=="Branches":
                for t,c in [("New",self.branch_new),("Switch",self.branch_switch),("Merge",self.branch_merge),("Delete",self.branch_delete),("Abort",lambda:self.run("merge","--abort"))]:ttk.Button(b,text=t,command=c).pack(side="left",padx=1,pady=3)
            elif n=="Stash":
                ttk.Button(b,text="Save",command=self.stash).pack(side="left");ttk.Button(b,text="Pop",command=lambda:self.run("stash","pop")).pack(side="left")
            elif n=="Tags":
                ttk.Button(b,text="Create",command=self.tag).pack(side="left");ttk.Button(b,text="Delete",command=self.tag_delete).pack(side="left");ttk.Button(b,text="Push tags",command=lambda:self.run("push","origin","--tags")).pack(side="left")
            elif n=="Remotes":ttk.Button(b,text="Add/update",command=self.remote).pack(side="left")
            x=tk.Text(f,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");x.pack(fill="both",expand=True);self.texts[n]=x
        if self.repo:self.refresh()
    def choose(self):
        p=filedialog.askdirectory(parent=self)
        if not p:return
        try:git(p,"rev-parse","--is-inside-work-tree")
        except Exception:
            if not messagebox.askyesno("Initialize", "Initialize this folder as a Git repository?",parent=self):return
            git(p,"init")
        self.repo=p;self.sel.set(p);self.refresh()
    def clone(self):
        u=simpledialog.askstring("Clone","Repository URL:",parent=self)
        if not u:return
        p=filedialog.askdirectory(parent=self)
        if p:self.safe(lambda:git(p,"clone",u),False)
    def safe(self,fn,refresh=True):
        try:o=fn();messagebox.showinfo("Git",o,parent=self)
        except Exception as e:messagebox.showerror("Git",str(e),parent=self);return
        if refresh:self.refresh()
    def run(self,*a):
        if self.repo:self.safe(lambda:git(self.repo,*a))
    def paths(self):return [self.files.item(i,"values")[1] for i in self.files.selection()]
    def refresh(self):
        if not self.repo:return
        try:
            status=git(self.repo,"status","--porcelain=v1");self.files.delete(*self.files.get_children())
            for i,l in enumerate(status.splitlines()):
                if len(l)>3:self.files.insert("","end",iid=str(i),values=(l[:2],l[3:]))
            data={"History":git(self.repo,"log","-100","--date=short","--pretty=format:%h  %ad  %an  %s"),"Branches":git(self.repo,"branch","-vv"),"Stash":git(self.repo,"stash","list"),"Tags":git(self.repo,"tag","--sort=-creatordate"),"Remotes":git(self.repo,"remote","-v"),"Conflicts":git(self.repo,"diff","--name-only","--diff-filter=U")}
            branch=git(self.repo,"branch","--show-current");self.sel.set(f"{self.repo}  |  {branch or 'detached HEAD'}")
            for n,v in data.items():self.texts[n].delete("1.0","end");self.texts[n].insert("1.0",v or ("No conflicts" if n=="Conflicts" else "None"))
        except Exception as e:messagebox.showerror("Refresh",str(e),parent=self)
    def stage(self):
        p=self.paths()
        if p:self.run("add","--",*p)
    def unstage(self):
        p=self.paths()
        if p:self.run("restore","--staged","--",*p)
    def commit(self):
        m=simpledialog.askstring("Commit","Commit message:",parent=self)
        if m:self.run("commit","-m",m)
    def diff(self):
        p=self.paths();a=["diff"]+(["--",p[0]] if p else [])
        try:self.output("Diff",git(self.repo,*a))
        except Exception as e:messagebox.showerror("Diff",str(e),parent=self)
    def discard(self):
        p=self.paths()
        if p and messagebox.askyesno("Discard","Permanently discard selected tracked-file changes?",parent=self):self.run("restore","--",*p)
    def clean(self):
        try:q=git(self.repo,"clean","-nd")
        except Exception as e:return messagebox.showerror("Clean",str(e),parent=self)
        if q=="Completed successfully.":return messagebox.showinfo("Clean","Nothing to clean",parent=self)
        if messagebox.askyesno("Clean",q+"\n\nDelete these untracked items permanently?",parent=self):self.run("clean","-fd")
    def branch_new(self):
        n=simpledialog.askstring("Branch","New branch name:",parent=self)
        if n:self.run("switch","-c",n)
    def branch_switch(self):
        n=simpledialog.askstring("Branch","Branch to switch to:",parent=self)
        if n:self.run("switch",n)
    def branch_merge(self):
        n=simpledialog.askstring("Merge","Branch to merge into current branch:",parent=self)
        if n and messagebox.askyesno("Merge",f"Merge {n}?",parent=self):self.run("merge","--no-edit",n)
    def branch_delete(self):
        n=simpledialog.askstring("Delete","Local branch name:",parent=self)
        if n and messagebox.askyesno("Delete",f"Delete {n}?",parent=self):self.run("branch","-d",n)
    def stash(self):
        m=simpledialog.askstring("Stash","Message:",parent=self) or "GitHub Command Center stash";self.run("stash","push","-u","-m",m)
    def tag(self):
        n=simpledialog.askstring("Tag","New annotated tag:",parent=self)
        if n:self.run("tag","-a",n,"-m",n)
    def tag_delete(self):
        n=simpledialog.askstring("Tag","Tag to delete locally:",parent=self)
        if n:self.run("tag","-d",n)
    def remote(self):
        n=simpledialog.askstring("Remote","Name:",initialvalue="origin",parent=self);u=simpledialog.askstring("Remote","URL:",parent=self) if n else None
        if u:
            try:git(self.repo,"remote","get-url",n);self.run("remote","set-url",n,u)
            except Exception:self.run("remote","add",n,u)
    def open_folder(self):
        import os
        if self.repo:os.startfile(self.repo) if hasattr(os,"startfile") else subprocess.Popen(["xdg-open",self.repo])
    def output(self,title,value):
        w=tk.Toplevel(self);w.title(title);w.geometry("900x600");t=tk.Text(w,wrap="none",font=("Consolas",9));t.pack(fill="both",expand=True);t.insert("1.0",value)

class CommitGraphWindow(tk.Toplevel):
    COLORS=("#60a5fa","#f472b6","#34d399","#fbbf24","#a78bfa","#22d3ee")
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Visual Commit History");self.geometry("1200x760")
        bar=ttk.Frame(self,padding=6);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.load).pack(side="left");ttk.Button(bar,text="Checkout selected",command=self.checkout).pack(side="left",padx=4)
        self.canvas=tk.Canvas(self,bg="#0b1220");ys=ttk.Scrollbar(self,orient="vertical",command=self.canvas.yview);self.canvas.configure(yscrollcommand=ys.set);ys.pack(side="right",fill="y");self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Button-1>",self.pick);self.selected=None;self.rows=[];self.load()
    def load(self):
        raw=git(self.repo,"log","--all","--topo-order","-250","--date=short","--pretty=format:%H%x1f%h%x1f%P%x1f%ad%x1f%an%x1f%s%x1f%D")
        self.data=[]
        for line in raw.splitlines():
            p=line.split("\x1f")
            if len(p)>=7:self.data.append(p)
        self.draw()
    def draw(self):
        c=self.canvas;c.delete("all");lanes={};next_lane=0;self.rows=[];rh=34
        for i,p in enumerate(self.data):
            full,short,parents,date,author,subject,refs=p;parents=parents.split()
            lane=lanes.pop(full,next_lane)
            if lane==next_lane:next_lane+=1
            if parents:lanes.setdefault(parents[0],lane)
            y=20+i*rh;x=24+lane*20;color=self.COLORS[lane%len(self.COLORS)]
            c.create_line(x,y-rh,x,y+rh,fill=color,width=2)
            for parent in parents[1:]:
                pl=lanes.setdefault(parent,next_lane)
                if pl==next_lane:next_lane+=1
                c.create_line(x,y,24+pl*20,y+rh,fill=self.COLORS[pl%len(self.COLORS)],width=2,smooth=True)
            c.create_oval(x-5,y-5,x+5,y+5,fill="#fbbf24" if self.selected==i else "white",outline=color,width=2)
            c.create_text(60+max(3,next_lane)*20,y,text=f"{short}  {subject}  {refs}  {author} · {date}",fill="#e2e8f0",anchor="w",font=("Consolas",9))
            self.rows.append((y-rh/2,y+rh/2,p))
        c.configure(scrollregion=(0,0,1800,max(100,len(self.data)*rh+40)))
    def pick(self,e):
        y=self.canvas.canvasy(e.y)
        for i,(a,b,p) in enumerate(self.rows):
            if a<=y<=b:self.selected=i;self.commit=p;self.draw();break
    def checkout(self):
        if self.selected is not None and messagebox.askyesno("Detached checkout",f"Checkout {self.commit[1]} in detached HEAD mode?",parent=self):
            try:git(self.repo,"switch","--detach",self.commit[0]);messagebox.showinfo("Checkout","Completed",parent=self)
            except Exception as e:messagebox.showerror("Checkout",str(e),parent=self)

class ConflictResolver(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Conflict Resolver");self.geometry("1400x800")
        out=git(repo,"diff","--name-only","--diff-filter=U");self.files=[x for x in out.splitlines() if x and x!="Completed successfully."]
        if not self.files:self.after(50,lambda:(messagebox.showinfo("Conflicts","No unresolved conflicts.",parent=self),self.destroy()));return
        top=ttk.Frame(self,padding=6);top.pack(fill="x");self.file=tk.StringVar(value=self.files[0]);box=ttk.Combobox(top,textvariable=self.file,values=self.files,state="readonly",width=60);box.pack(side="left");box.bind("<<ComboboxSelected>>",lambda e:self.load())
        for t,c in [("Use ours",lambda:self.use("--ours")),("Use theirs",lambda:self.use("--theirs")),("Save",self.save),("Save + mark resolved",self.resolve),("Abort merge",self.abort)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=6,pady=6)
        self.ours=self.panel(pane,"OURS",False);self.merged=self.panel(pane,"MERGED RESULT",True);self.theirs=self.panel(pane,"THEIRS",False)
        for x in (self.ours,self.merged,self.theirs):pane.add(x[0],weight=1)
        self.load()
    def panel(self,parent,title,edit):
        f=ttk.Frame(parent);ttk.Label(f,text=title,font=("Segoe UI Semibold",10)).pack(anchor="w");t=tk.Text(f,wrap="none",undo=edit,font=("Consolas",9));t.pack(fill="both",expand=True)
        if not edit:t.config(state="disabled")
        return f,t
    def put(self,panel,value,lock=False):
        t=panel[1];t.config(state="normal");t.delete("1.0","end");t.insert("1.0",value)
        if lock:t.config(state="disabled")
    def version(self,n,p):
        try:return git(self.repo,"show",f":{n}:{p}")
        except:return "(unavailable)"
    def load(self):
        p=self.file.get();self.put(self.ours,self.version(2,p),True);self.put(self.theirs,self.version(3,p),True)
        try:v=(Path(self.repo)/p).read_text(encoding="utf-8",errors="replace")
        except:v=""
        self.put(self.merged,v)
    def use(self,side):
        if messagebox.askyesno("Replace",f"Use {side[2:]} version?",parent=self):git(self.repo,"checkout",side,"--",self.file.get());self.load()
    def save(self):(Path(self.repo)/self.file.get()).write_text(self.merged[1].get("1.0","end-1c"),encoding="utf-8")
    def resolve(self):
        self.save();git(self.repo,"add","--",self.file.get());self.files.remove(self.file.get())
        if not self.files:messagebox.showinfo("Resolved","All conflicts are staged. Commit to complete the merge.",parent=self);self.destroy()
        else:self.file.set(self.files[0]);self.load()
    def abort(self):
        if messagebox.askyesno("Abort merge","Abort the merge?",parent=self):git(self.repo,"merge","--abort");self.destroy()

class AdvancedGitWindow(tk.Toplevel):
    """Safe guided workflows for operations commonly hidden in Git context menus."""
    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.title("Advanced Git Operations")
        self.geometry("980x700")
        self.minsize(850, 600)
        self._build()
        self.refresh()

    def _build(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text=self.repo, font=("Segoe UI Semibold", 11)).pack(side="left", fill="x", expand=True)
        ttk.Button(header, text="Refresh", command=self.refresh).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cherry = ttk.Frame(self.tabs, padding=10)
        self.rebase = ttk.Frame(self.tabs, padding=10)
        self.reset = ttk.Frame(self.tabs, padding=10)
        self.ignore = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.cherry, text="Cherry-pick")
        self.tabs.add(self.rebase, text="Rebase")
        self.tabs.add(self.reset, text="Reset & Revert")
        self.tabs.add(self.ignore, text=".gitignore")

        ttk.Label(self.cherry, text="Recent commits", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.commit_list = tk.Listbox(self.cherry, font=("Consolas", 9), height=18)
        self.commit_list.pack(fill="both", expand=True, pady=6)
        row = ttk.Frame(self.cherry); row.pack(fill="x")
        ttk.Button(row, text="Cherry-pick selected", command=self.cherry_pick).pack(side="left")
        ttk.Button(row, text="Abort cherry-pick", command=lambda:self.execute(["cherry-pick", "--abort"], confirm="Abort the current cherry-pick?" )).pack(side="left", padx=4)
        ttk.Button(row, text="Continue cherry-pick", command=lambda:self.execute(["cherry-pick", "--continue"])).pack(side="left")

        ttk.Label(self.rebase, text="Rebase the current branch onto another branch", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.branch_var = tk.StringVar()
        self.branch_box = ttk.Combobox(self.rebase, textvariable=self.branch_var, state="readonly")
        self.branch_box.pack(fill="x", pady=8)
        ttk.Label(self.rebase, text="A safety branch is created before rebase. Working tree must be clean.", foreground="#9a3412").pack(anchor="w", pady=(0, 10))
        rb = ttk.Frame(self.rebase); rb.pack(fill="x")
        ttk.Button(rb, text="Start safe rebase", command=self.start_rebase).pack(side="left")
        ttk.Button(rb, text="Continue", command=lambda:self.execute(["rebase", "--continue"])).pack(side="left", padx=4)
        ttk.Button(rb, text="Skip", command=lambda:self.execute(["rebase", "--skip"], confirm="Skip the current commit?" )).pack(side="left")
        ttk.Button(rb, text="Abort", command=lambda:self.execute(["rebase", "--abort"], confirm="Abort this rebase?" )).pack(side="left", padx=4)

        ttk.Label(self.reset, text="Revert creates a new undo commit and is the recommended shared-history option.", wraplength=800).pack(anchor="w", pady=(0, 8))
        self.hash_var = tk.StringVar()
        ttk.Entry(self.reset, textvariable=self.hash_var).pack(fill="x", pady=4)
        rr = ttk.Frame(self.reset); rr.pack(fill="x", pady=6)
        ttk.Button(rr, text="Revert commit", command=self.revert_commit).pack(side="left")
        ttk.Button(rr, text="Reset soft", command=lambda:self.reset_to("--soft")).pack(side="left", padx=4)
        ttk.Button(rr, text="Reset mixed", command=lambda:self.reset_to("--mixed")).pack(side="left")
        ttk.Button(rr, text="Reset hard", command=lambda:self.reset_to("--hard")).pack(side="left", padx=4)
        ttk.Label(self.reset, text="Hard reset permanently discards tracked working-tree and index changes. A backup branch is created first.", foreground="#b91c1c", wraplength=800).pack(anchor="w", pady=8)

        ttk.Label(self.ignore, text="Repository .gitignore editor", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.ignore_text = tk.Text(self.ignore, wrap="none", undo=True, font=("Consolas", 10))
        self.ignore_text.pack(fill="both", expand=True, pady=6)
        ig = ttk.Frame(self.ignore); ig.pack(fill="x")
        ttk.Button(ig, text="Save .gitignore", command=self.save_ignore).pack(side="left")
        ttk.Button(ig, text="Add common Python rules", command=lambda:self.add_ignore("__pycache__/\n*.py[cod]\n.venv/\ndist/\nbuild/\n*.egg-info/\n.env\n")).pack(side="left", padx=4)
        ttk.Button(ig, text="Add common Node rules", command=lambda:self.add_ignore("node_modules/\ndist/\n.env\n*.log\ncoverage/\n")).pack(side="left")

    def refresh(self):
        try:
            commits = git(self.repo, "log", "--all", "-100", "--pretty=format:%H%x09%h%x09%s")
            self.commit_rows = []
            self.commit_list.delete(0, "end")
            for line in commits.splitlines():
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    self.commit_rows.append(parts)
                    self.commit_list.insert("end", f"{parts[1]}  {parts[2]}")
            branch_text = git(self.repo, "branch", "--format=%(refname:short)")
            branches = [x for x in branch_text.splitlines() if x and x != "Completed successfully."]
            self.branch_box["values"] = branches
            if branches and not self.branch_var.get(): self.branch_var.set(branches[0])
            path = Path(self.repo) / ".gitignore"
            self.ignore_text.delete("1.0", "end")
            if path.exists(): self.ignore_text.insert("1.0", path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            messagebox.showerror("Advanced Git", str(exc), parent=self)

    def execute(self, args, confirm=None):
        if confirm and not messagebox.askyesno("Confirm", confirm, parent=self): return
        try:
            out = git(self.repo, *args)
            messagebox.showinfo("Git", out, parent=self)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Git", str(exc), parent=self)

    def backup_branch(self, prefix):
        import datetime
        name = f"gccc-backup/{prefix}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        git(self.repo, "branch", name)
        return name

    def clean_required(self):
        state = git(self.repo, "status", "--porcelain")
        if state != "Completed successfully.":
            messagebox.showwarning("Clean working tree required", "Commit or stash changes before this operation.", parent=self)
            return False
        return True

    def cherry_pick(self):
        sel = self.commit_list.curselection()
        if not sel: return
        full, short, subject = self.commit_rows[sel[0]]
        if messagebox.askyesno("Cherry-pick", f"Apply {short} {subject} onto the current branch?", parent=self):
            self.execute(["cherry-pick", full])

    def start_rebase(self):
        target = self.branch_var.get()
        if not target or not self.clean_required(): return
        try:
            backup = self.backup_branch("pre-rebase")
            if not messagebox.askyesno("Safe rebase", f"Backup branch created:\n{backup}\n\nRebase current branch onto {target}?", parent=self): return
            self.execute(["rebase", target])
        except Exception as exc: messagebox.showerror("Rebase", str(exc), parent=self)

    def revert_commit(self):
        value = self.hash_var.get().strip()
        if value and messagebox.askyesno("Revert", f"Create a new commit reverting {value}?", parent=self): self.execute(["revert", "--no-edit", value])

    def reset_to(self, mode):
        value = self.hash_var.get().strip()
        if not value: return
        warning = f"Reset current branch to {value} using {mode}?"
        if mode == "--hard": warning += "\n\nTracked local changes will be permanently discarded."
        if not messagebox.askyesno("Reset", warning, parent=self): return
        try:
            backup = self.backup_branch("pre-reset")
            if messagebox.askyesno("Backup created", f"Created {backup}. Continue with reset?", parent=self): self.execute(["reset", mode, value])
        except Exception as exc: messagebox.showerror("Reset", str(exc), parent=self)

    def add_ignore(self, value):
        current = self.ignore_text.get("1.0", "end-1c")
        if current and not current.endswith("\n"): self.ignore_text.insert("end", "\n")
        self.ignore_text.insert("end", value)

    def save_ignore(self):
        try:
            (Path(self.repo) / ".gitignore").write_text(self.ignore_text.get("1.0", "end-1c") + "\n", encoding="utf-8")
            messagebox.showinfo(".gitignore", "Saved. Stage the file when ready.", parent=self)
        except Exception as exc: messagebox.showerror(".gitignore", str(exc), parent=self)

class ReleaseCenter(tk.Toplevel):
    """Guided tag, GitHub release, asset upload, bundle backup, and release-readiness UI."""
    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.assets = []
        self.title("Release Center")
        self.geometry("1050x780")
        self.minsize(900, 680)
        self._build()
        self.refresh()

    def _build(self):
        head = ttk.Frame(self, padding=10); head.pack(fill="x")
        ttk.Label(head, text=self.repo, font=("Segoe UI Semibold", 11)).pack(side="left", fill="x", expand=True)
        ttk.Button(head, text="Refresh readiness", command=self.refresh).pack(side="right")
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.ready = ttk.Frame(self.tabs, padding=12); self.publish = ttk.Frame(self.tabs, padding=12); self.bundle = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.ready, text="Release readiness"); self.tabs.add(self.publish, text="Publish release"); self.tabs.add(self.bundle, text="Backup & export")

        self.readiness = tk.Text(self.ready, wrap="word", font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0")
        self.readiness.pack(fill="both", expand=True)

        form = ttk.Frame(self.publish); form.pack(fill="x")
        self.tag_var = tk.StringVar(); self.title_var = tk.StringVar(); self.target_var = tk.StringVar(); self.draft_var = tk.BooleanVar(); self.pre_var = tk.BooleanVar()
        for row,(label,var) in enumerate((("Version tag",self.tag_var),("Release title",self.title_var),("Target branch",self.target_var))):
            ttk.Label(form,text=label).grid(row=row,column=0,sticky="w",pady=4); ttk.Entry(form,textvariable=var).grid(row=row,column=1,sticky="ew",padx=8,pady=4)
        form.columnconfigure(1,weight=1)
        flags=ttk.Frame(self.publish);flags.pack(fill="x",pady=6)
        ttk.Checkbutton(flags,text="Draft release",variable=self.draft_var).pack(side="left")
        ttk.Checkbutton(flags,text="Pre-release",variable=self.pre_var).pack(side="left",padx=12)
        ttk.Label(self.publish,text="Release notes (Markdown)",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=(8,3))
        self.notes=tk.Text(self.publish,height=14,wrap="word",font=("Consolas",9));self.notes.pack(fill="both",expand=True)
        ab=ttk.Frame(self.publish);ab.pack(fill="x",pady=6)
        ttk.Button(ab,text="Generate notes from commits",command=self.generate_notes).pack(side="left")
        ttk.Button(ab,text="Add assets",command=self.add_assets).pack(side="left",padx=4)
        self.asset_label=ttk.Label(ab,text="No assets selected");self.asset_label.pack(side="left",padx=8)
        ttk.Button(self.publish,text="Create tag, push, and publish GitHub release",command=self.publish_release).pack(anchor="e",pady=8)

        ttk.Label(self.bundle,text="Portable Git bundle backup",font=("Segoe UI Semibold",11)).pack(anchor="w")
        ttk.Label(self.bundle,text="A .bundle file contains all branches and tags and can recreate the repository without GitHub.",wraplength=800).pack(anchor="w",pady=(2,8))
        ttk.Button(self.bundle,text="Create full repository bundle",command=self.create_bundle).pack(anchor="w")
        ttk.Separator(self.bundle).pack(fill="x",pady=18)
        ttk.Label(self.bundle,text="Repository archive",font=("Segoe UI Semibold",11)).pack(anchor="w")
        ttk.Label(self.bundle,text="Create a clean ZIP of the current HEAD without the .git directory.",wraplength=800).pack(anchor="w",pady=(2,8))
        ttk.Button(self.bundle,text="Export current HEAD as ZIP",command=self.export_zip).pack(anchor="w")
        ttk.Separator(self.bundle).pack(fill="x",pady=18)
        ttk.Label(self.bundle,text="Recovery commands",font=("Segoe UI Semibold",11)).pack(anchor="w")
        self.recovery=tk.Text(self.bundle,height=10,wrap="none",font=("Consolas",9),bg="#f8fafc");self.recovery.pack(fill="x",pady=6)
        self.recovery.insert("1.0","Clone from a bundle:\n  git clone repository.bundle recovered-repository\n\nVerify a bundle:\n  git bundle verify repository.bundle\n\nList contained references:\n  git bundle list-heads repository.bundle")
        self.recovery.config(state="disabled")

    def gh(self,*args):
        try:
            r=subprocess.run(["gh",*args],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
        except FileNotFoundError: raise GitError("GitHub CLI (gh) is not installed or is not on PATH. Install it, then run 'gh auth login'.")
        out=(r.stdout+"\n"+r.stderr).strip()
        if r.returncode: raise GitError(out or "GitHub CLI command failed")
        return out or "Completed successfully."

    def refresh(self):
        checks=[]
        def check(name,ok,detail):checks.append(("PASS" if ok else "WARN",name,detail))
        try:
            status=git(self.repo,"status","--porcelain")
            check("Working tree clean",status=="Completed successfully.","Clean" if status=="Completed successfully." else "Commit or stash local changes")
            branch=git(self.repo,"branch","--show-current");check("On a branch",branch!="Completed successfully." and bool(branch),branch)
            remote=git(self.repo,"remote","get-url","origin");check("Origin remote",bool(remote),remote)
            try: upstream=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");check("Upstream configured",True,upstream)
            except Exception: check("Upstream configured",False,"Push with upstream before release")
            try:
                behind=git(self.repo,"rev-list","--count","HEAD..@{u}");ahead=git(self.repo,"rev-list","--count","@{u}..HEAD")
                check("Remote synchronization",behind in ("0","Completed successfully."),f"Ahead {ahead}; behind {behind}")
            except Exception:check("Remote synchronization",False,"Unable to compare with upstream")
            for filename in ("README.md","CHANGELOG.md","LICENSE"):
                check(filename,(Path(self.repo)/filename).exists(),"Present" if (Path(self.repo)/filename).exists() else "Missing")
            try:self.gh("--version");check("GitHub CLI",True,"Available")
            except Exception as e:check("GitHub CLI",False,str(e))
            self.target_var.set(branch if branch!="Completed successfully." else "main")
            self.readiness.config(state="normal");self.readiness.delete("1.0","end")
            self.readiness.insert("1.0","RELEASE READINESS REPORT\n"+"="*72+"\n\n")
            for state,name,detail in checks:self.readiness.insert("end",f"[{state:4}] {name}\n       {detail}\n\n")
            self.readiness.config(state="disabled")
        except Exception as exc:messagebox.showerror("Readiness",str(exc),parent=self)

    def generate_notes(self):
        try:
            last=git(self.repo,"describe","--tags","--abbrev=0")
            args=["log","--pretty=format:- %s (%h)"]
            if last!="Completed successfully.":args.append(f"{last}..HEAD")
            notes=git(self.repo,*args)
            self.notes.delete("1.0","end");self.notes.insert("1.0",f"## What's changed\n\n{notes}\n")
        except Exception as exc:messagebox.showerror("Release notes",str(exc),parent=self)

    def add_assets(self):
        files=filedialog.askopenfilenames(title="Select release assets",parent=self)
        if files:self.assets=list(files);self.asset_label.config(text=f"{len(files)} asset(s) selected")

    def publish_release(self):
        tag=self.tag_var.get().strip();title=self.title_var.get().strip() or tag;target=self.target_var.get().strip();notes=self.notes.get("1.0","end-1c").strip()
        if not tag:return messagebox.showwarning("Release","Enter a version tag such as v0.5.0.",parent=self)
        if not re.match(r"^[A-Za-z0-9._/-]+$",tag):return messagebox.showwarning("Release","Tag contains unsupported characters.",parent=self)
        summary=f"Tag: {tag}\nTitle: {title}\nTarget: {target}\nAssets: {len(self.assets)}\n\nCreate and publish this release?"
        if not messagebox.askyesno("Publish release",summary,parent=self):return
        try:
            status=git(self.repo,"status","--porcelain")
            if status!="Completed successfully.":raise GitError("Working tree is not clean. Commit or stash changes first.")
            existing=git(self.repo,"tag","--list",tag)
            if existing=="Completed successfully.":git(self.repo,"tag","-a",tag,"-m",title)
            git(self.repo,"push","origin",tag)
            args=["release","create",tag,"--title",title,"--notes",notes or title]
            if target:args += ["--target",target]
            if self.draft_var.get():args.append("--draft")
            if self.pre_var.get():args.append("--prerelease")
            args += self.assets
            out=self.gh(*args);messagebox.showinfo("Release published",out,parent=self);self.refresh()
        except Exception as exc:messagebox.showerror("Release failed",str(exc),parent=self)

    def create_bundle(self):
        default=(self.tag_var.get().strip() or Path(self.repo).name)+"-full.bundle"
        path=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=default,filetypes=[("Git bundle","*.bundle")])
        if path:
            try:out=git(self.repo,"bundle","create",path,"--all");messagebox.showinfo("Bundle",f"{out}\n\nSaved: {path}",parent=self)
            except Exception as exc:messagebox.showerror("Bundle",str(exc),parent=self)

    def export_zip(self):
        default=(self.tag_var.get().strip() or Path(self.repo).name)+".zip"
        path=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",initialfile=default,filetypes=[("ZIP archive","*.zip")])
        if path:
            try:out=git(self.repo,"archive","--format=zip",f"--output={path}","HEAD");messagebox.showinfo("Archive",f"{out}\n\nSaved: {path}",parent=self)
            except Exception as exc:messagebox.showerror("Archive",str(exc),parent=self)

class PullRequestCenter(tk.Toplevel):
    """GitHub CLI based pull-request workflow integrated into the desktop app."""
    def __init__(self, parent, repo):
        super().__init__(parent); self.repo=repo
        self.title("Pull Request Center"); self.geometry("1180x760"); self.minsize(950,650)
        self.rows=[]; self._build(); self.refresh()
    def gh(self,*args):
        try:r=subprocess.run(["gh",*args],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
        except FileNotFoundError:raise GitError("GitHub CLI (gh) is required. Install it and run 'gh auth login'.")
        out=(r.stdout+"\n"+r.stderr).strip()
        if r.returncode:raise GitError(out or "GitHub CLI command failed")
        return out
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        ttk.Label(top,text=self.repo,font=("Segoe UI Semibold",11)).pack(side="left",fill="x",expand=True)
        for t,c in [("Refresh",self.refresh),("Create PR",self.create_pr),("Checkout",self.checkout),("Merge",self.merge),("Open",self.open_pr)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5)
        left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=3);pane.add(right,weight=2)
        self.tree=ttk.Treeview(left,columns=("num","title","author","branch","state"),show="headings")
        for c,t,w in [("num","#",55),("title","Title",330),("author","Author",120),("branch","Branch",170),("state","State",80)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.detail=tk.Text(right,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.detail.pack(fill="both",expand=True)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def refresh(self):
        try:
            import json
            raw=self.gh("pr","list","--limit","100","--state","all","--json","number,title,author,headRefName,state,url,isDraft")
            self.rows=json.loads(raw or "[]");self.tree.delete(*self.tree.get_children())
            for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r["number"],r["title"],(r.get("author") or {}).get("login",""),r.get("headRefName",""),("DRAFT" if r.get("isDraft") else r.get("state",""))))
        except Exception as e:messagebox.showerror("Pull Requests",str(e),parent=self)
    def details(self):
        r=self.selected()
        if not r:return
        try:out=self.gh("pr","view",str(r["number"]),"--comments");self.detail.delete("1.0","end");self.detail.insert("1.0",out)
        except Exception as e:messagebox.showerror("PR details",str(e),parent=self)
    def create_pr(self):
        branch=git(self.repo,"branch","--show-current");title=simpledialog.askstring("Create PR","Title:",parent=self)
        if not title:return
        body=simpledialog.askstring("Create PR","Description:",parent=self) or ""
        base=simpledialog.askstring("Create PR","Base branch:",initialvalue="main",parent=self) or "main"
        if messagebox.askyesno("Create PR",f"Create PR from {branch} into {base}?",parent=self):
            try:out=self.gh("pr","create","--title",title,"--body",body,"--base",base,"--head",branch);messagebox.showinfo("Pull Request",out,parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Create PR",str(e),parent=self)
    def checkout(self):
        r=self.selected()
        if r:
            try:messagebox.showinfo("Checkout",self.gh("pr","checkout",str(r["number"])),parent=self)
            except Exception as e:messagebox.showerror("Checkout",str(e),parent=self)
    def merge(self):
        r=self.selected()
        if not r:return
        method=simpledialog.askstring("Merge PR","Method: merge, squash, or rebase",initialvalue="squash",parent=self)
        if method not in ("merge","squash","rebase"):return
        if messagebox.askyesno("Merge PR",f"Merge PR #{r['number']} using {method}?",parent=self):
            try:out=self.gh("pr","merge",str(r["number"]),f"--{method}","--delete-branch");messagebox.showinfo("Merge",out,parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Merge",str(e),parent=self)
    def open_pr(self):
        r=self.selected()
        if r:
            import webbrowser;webbrowser.open(r["url"])

class ActionsCenter(tk.Toplevel):
    """GitHub Actions dashboard and workflow controls."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("GitHub Actions Center");self.geometry("1150x740");self.minsize(900,620);self.rows=[];self._build();self.refresh()
    def gh(self,*args):
        try:r=subprocess.run(["gh",*args],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
        except FileNotFoundError:raise GitError("GitHub CLI (gh) is required. Install it and run 'gh auth login'.")
        out=(r.stdout+"\n"+r.stderr).strip()
        if r.returncode:raise GitError(out or "GitHub CLI command failed")
        return out
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("View log",self.log),("Re-run",self.rerun),("Cancel",self.cancel),("Run workflow",self.workflow)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("id","workflow","branch","event","status","result","created"),show="headings")
        for c,t,w in [("id","Run",90),("workflow","Workflow",260),("branch","Branch",150),("event","Event",90),("status","Status",100),("result","Result",100),("created","Created",160)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def refresh(self):
        try:
            import json
            raw=self.gh("run","list","--limit","100","--json","databaseId,workflowName,headBranch,event,status,conclusion,createdAt,url")
            self.rows=json.loads(raw or "[]");self.tree.delete(*self.tree.get_children())
            for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r["databaseId"],r.get("workflowName",""),r.get("headBranch",""),r.get("event",""),r.get("status",""),r.get("conclusion") or "-",r.get("createdAt","")))
        except Exception as e:messagebox.showerror("Actions",str(e),parent=self)
    def log(self):
        r=self.selected()
        if not r:return
        try:self.output("Workflow log",self.gh("run","view",str(r["databaseId"]),"--log"))
        except Exception as e:messagebox.showerror("Actions",str(e),parent=self)
    def rerun(self):
        r=self.selected()
        if r and messagebox.askyesno("Re-run",f"Re-run workflow {r['databaseId']}?",parent=self):
            try:messagebox.showinfo("Actions",self.gh("run","rerun",str(r["databaseId"])),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Actions",str(e),parent=self)
    def cancel(self):
        r=self.selected()
        if r and messagebox.askyesno("Cancel",f"Cancel workflow {r['databaseId']}?",parent=self):
            try:messagebox.showinfo("Actions",self.gh("run","cancel",str(r["databaseId"])),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Actions",str(e),parent=self)
    def workflow(self):
        try:
            raw=self.gh("workflow","list");name=simpledialog.askstring("Run workflow","Workflow name or ID:\n\n"+raw,parent=self)
            if name:messagebox.showinfo("Workflow",self.gh("workflow","run",name),parent=self)
        except Exception as e:messagebox.showerror("Workflow",str(e),parent=self)
    def output(self,title,value):
        w=tk.Toplevel(self);w.title(title);w.geometry("1000x650");t=tk.Text(w,wrap="none",font=("Consolas",9));t.pack(fill="both",expand=True);t.insert("1.0",value)

class SecurityCenter(tk.Toplevel):
    """Repository security overview using GitHub CLI API and local Git checks."""
    def __init__(self, parent, repo):
        super().__init__(parent); self.repo=repo
        self.title("Security & Dependency Center"); self.geometry("1220x780"); self.minsize(980,650)
        self.rows=[]; self._build(); self.refresh_all()

    def gh(self, *args):
        try:
            r=subprocess.run(["gh",*args],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
        except FileNotFoundError:
            raise GitError("GitHub CLI (gh) is required. Install it and run 'gh auth login'.")
        out=(r.stdout+"\n"+r.stderr).strip()
        if r.returncode: raise GitError(out or "GitHub CLI command failed")
        return out

    def repo_slug(self):
        import re
        url=git(self.repo,"remote","get-url","origin")
        m=re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",url)
        if not m: raise GitError("The origin remote is not a GitHub repository.")
        return f"{m.group(1)}/{m.group(2)}"

    def _build(self):
        top=ttk.Frame(self,padding=8); top.pack(fill="x")
        ttk.Label(top,text=self.repo,font=("Segoe UI Semibold",11)).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Refresh all",command=self.refresh_all).pack(side="right")
        self.tabs=ttk.Notebook(self); self.tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self.summary=ttk.Frame(self.tabs,padding=10); self.dependabot=ttk.Frame(self.tabs,padding=8); self.code=ttk.Frame(self.tabs,padding=8); self.secret=ttk.Frame(self.tabs,padding=8); self.local=ttk.Frame(self.tabs,padding=8)
        for frame,title in [(self.summary,"Security summary"),(self.dependabot,"Dependabot"),(self.code,"Code scanning"),(self.secret,"Secret scanning"),(self.local,"Local audit")]: self.tabs.add(frame,text=title)
        self.summary_text=tk.Text(self.summary,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0"); self.summary_text.pack(fill="both",expand=True)
        self.dep_tree=self.make_tree(self.dependabot,("number","severity","package","manifest","state"),("#","Severity","Package","Manifest","State"),(60,90,220,260,90))
        depbar=ttk.Frame(self.dependabot);depbar.pack(fill="x",pady=5);ttk.Button(depbar,text="Open selected alert",command=lambda:self.open_alert(self.dep_tree)).pack(side="left")
        self.code_tree=self.make_tree(self.code,("number","severity","rule","tool","state"),("#","Severity","Rule","Tool","State"),(60,90,330,170,90))
        codebar=ttk.Frame(self.code);codebar.pack(fill="x",pady=5);ttk.Button(codebar,text="Open selected alert",command=lambda:self.open_alert(self.code_tree)).pack(side="left")
        self.secret_tree=self.make_tree(self.secret,("number","type","location","state"),("#","Secret type","Location","State"),(60,260,430,90))
        secbar=ttk.Frame(self.secret);secbar.pack(fill="x",pady=5);ttk.Button(secbar,text="Open selected alert",command=lambda:self.open_alert(self.secret_tree)).pack(side="left")
        localbar=ttk.Frame(self.local);localbar.pack(fill="x")
        for t,c in [("Run Git checks",self.local_checks),("Run pip-audit",self.pip_audit),("Run Bandit",self.bandit),("Generate checksums",self.checksums)]:ttk.Button(localbar,text=t,command=c).pack(side="left",padx=2)
        self.local_text=tk.Text(self.local,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.local_text.pack(fill="both",expand=True,pady=6)

    def make_tree(self,parent,cols,labels,widths):
        tree=ttk.Treeview(parent,columns=cols,show="headings")
        for c,l,w in zip(cols,labels,widths):tree.heading(c,text=l);tree.column(c,width=w,anchor="w")
        tree.pack(fill="both",expand=True);return tree

    def api_json(self,path):
        import json
        out=self.gh("api","-H","Accept: application/vnd.github+json",path,"--paginate")
        return json.loads(out or "[]")

    def refresh_all(self):
        try:
            slug=self.repo_slug(); self.slug=slug
            errors=[]
            try:self.dep_rows=self.api_json(f"repos/{slug}/dependabot/alerts?per_page=100&state=open")
            except Exception as e:self.dep_rows=[];errors.append("Dependabot: "+str(e))
            try:self.code_rows=self.api_json(f"repos/{slug}/code-scanning/alerts?per_page=100&state=open")
            except Exception as e:self.code_rows=[];errors.append("Code scanning: "+str(e))
            try:self.secret_rows=self.api_json(f"repos/{slug}/secret-scanning/alerts?per_page=100&state=open")
            except Exception as e:self.secret_rows=[];errors.append("Secret scanning: "+str(e))
            self.fill_alerts(); self.fill_summary(errors); self.local_checks()
        except Exception as e:messagebox.showerror("Security Center",str(e),parent=self)

    def fill_alerts(self):
        self.dep_tree.delete(*self.dep_tree.get_children())
        for i,a in enumerate(self.dep_rows):
            package=(a.get("dependency") or {}).get("package",{}).get("name",""); manifest=(a.get("dependency") or {}).get("manifest_path",""); sev=(a.get("security_advisory") or {}).get("severity","")
            self.dep_tree.insert("","end",iid=str(i),values=(a.get("number"),sev,package,manifest,a.get("state")),tags=(a.get("html_url","") or "",))
        self.code_tree.delete(*self.code_tree.get_children())
        for i,a in enumerate(self.code_rows):
            rule=a.get("rule") or {};tool=(a.get("tool") or {}).get("name","")
            self.code_tree.insert("","end",iid=str(i),values=(a.get("number"),rule.get("security_severity_level") or rule.get("severity"),rule.get("description") or rule.get("id"),tool,a.get("state")),tags=(a.get("html_url","") or "",))
        self.secret_tree.delete(*self.secret_tree.get_children())
        for i,a in enumerate(self.secret_rows):
            loc=((a.get("locations") or [{}])[0].get("details") or {}).get("path","")
            self.secret_tree.insert("","end",iid=str(i),values=(a.get("number"),a.get("secret_type_display_name") or a.get("secret_type"),loc,a.get("state")),tags=(a.get("html_url","") or "",))

    def fill_summary(self,errors):
        high=sum(1 for a in self.dep_rows if (a.get("security_advisory") or {}).get("severity") in ("high","critical"))
        text=(f"SECURITY SUMMARY FOR {self.slug}\n"+"="*72+"\n\n"
              f"Open Dependabot alerts : {len(self.dep_rows)}\n"
              f"High/Critical dependencies: {high}\n"
              f"Open code-scanning alerts: {len(self.code_rows)}\n"
              f"Open secret-scanning alerts: {len(self.secret_rows)}\n\n")
        if errors:text += "FEATURE OR PERMISSION WARNINGS\n"+"-"*72+"\n"+"\n".join("- "+e for e in errors)+"\n\n"
        text += "Recommended order:\n1. Revoke and rotate exposed secrets immediately.\n2. Fix critical/high dependency alerts.\n3. Review code-scanning alerts.\n4. Commit lockfiles and rerun CI.\n"
        self.summary_text.delete("1.0","end");self.summary_text.insert("1.0",text)

    def open_alert(self,tree):
        sel=tree.selection()
        if not sel:return
        tags=tree.item(sel[0],"tags")
        if tags and tags[0]:
            import webbrowser;webbrowser.open(tags[0])

    def set_local(self,title,text):
        self.local_text.delete("1.0","end");self.local_text.insert("1.0",title+"\n"+"="*72+"\n\n"+text)

    def local_checks(self):
        try:
            lines=[]
            tracked=git(self.repo,"ls-files")
            suspicious=[x for x in tracked.splitlines() if x.lower().endswith((".pem",".key",".pfx",".p12",".env")) or "credential" in x.lower() or "secret" in x.lower()]
            lines.append("Potentially sensitive tracked filenames:\n"+("\n".join("  - "+x for x in suspicious) if suspicious else "  None detected by filename"))
            large=[]
            for f in tracked.splitlines():
                p=Path(self.repo)/f
                try:
                    if p.is_file() and p.stat().st_size>10*1024*1024:large.append(f"{f} ({p.stat().st_size/1024/1024:.1f} MB)")
                except OSError:pass
            lines.append("\nTracked files over 10 MB:\n"+("\n".join("  - "+x for x in large) if large else "  None"))
            lines.append("\nGit fsck:\n"+git(self.repo,"fsck","--no-progress"))
            self.set_local("LOCAL REPOSITORY AUDIT","\n".join(lines))
        except Exception as e:self.set_local("LOCAL REPOSITORY AUDIT","ERROR: "+str(e))

    def external_scan(self,cmd,title):
        try:
            r=subprocess.run(cmd,cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace")
            self.set_local(title,(r.stdout+"\n"+r.stderr).strip() or "No findings reported.")
        except FileNotFoundError:self.set_local(title,f"Tool not installed. Install with: python -m pip install {cmd[0]}")
        except Exception as e:self.set_local(title,"ERROR: "+str(e))
    def pip_audit(self):self.external_scan(["pip-audit","-r","requirements.txt"],"PIP-AUDIT RESULTS")
    def bandit(self):self.external_scan(["bandit","-r",".","-x",".venv,venv"],"BANDIT RESULTS")
    def checksums(self):
        import hashlib
        files=filedialog.askopenfilenames(title="Select release files",parent=self)
        if not files:return
        lines=[]
        for name in files:
            h=hashlib.sha256()
            with open(name,"rb") as f:
                for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
            lines.append(f"{h.hexdigest()}  {Path(name).name}")
        target=filedialog.asksaveasfilename(title="Save checksums",defaultextension=".txt",initialfile="SHA256SUMS.txt",parent=self)
        if target:Path(target).write_text("\n".join(lines)+"\n",encoding="utf-8");messagebox.showinfo("Checksums",f"Saved {target}",parent=self)

class RepositoryHealthCenter(tk.Toplevel):
    """Repository hygiene, documentation quality and maintenance dashboard."""
    def __init__(self, parent, repo):
        super().__init__(parent); self.repo=repo
        self.title("Repository Health Center"); self.geometry("1180x780"); self.minsize(950,650)
        self._build(); self.refresh()

    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        ttk.Label(top,text=self.repo,font=("Segoe UI Semibold",11)).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Refresh audit",command=self.refresh).pack(side="right")
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self.score_tab=ttk.Frame(self.tabs,padding=10);self.files_tab=ttk.Frame(self.tabs,padding=10);self.templates_tab=ttk.Frame(self.tabs,padding=10)
        self.tabs.add(self.score_tab,text="Health score");self.tabs.add(self.files_tab,text="Repository files");self.tabs.add(self.templates_tab,text="Templates")
        self.score=tk.Text(self.score_tab,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.score.pack(fill="both",expand=True)
        self.files=tk.Text(self.files_tab,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.files.pack(fill="both",expand=True)
        row=ttk.Frame(self.templates_tab);row.pack(fill="x",pady=(0,8))
        for title,fn in [("Create SECURITY.md",self.security_md),("Create CONTRIBUTING.md",self.contributing_md),("Create issue templates",self.issue_templates),("Create PR template",self.pr_template),("Create CODEOWNERS",self.codeowners),("Create .gitattributes",self.gitattributes)]:ttk.Button(row,text=title,command=fn).pack(side="left",padx=2,pady=2)
        self.template_info=tk.Text(self.templates_tab,wrap="word",font=("Segoe UI",10));self.template_info.pack(fill="both",expand=True)
        self.template_info.insert("1.0","Generate common repository-governance files directly into the working tree. Existing files are never overwritten without confirmation. Review and commit generated files through Local Git.")
        self.template_info.config(state="disabled")

    def present(self, rel): return (Path(self.repo)/rel).exists()
    def age_days(self, rel):
        p=Path(self.repo)/rel
        if not p.exists():return None
        import time
        return int((time.time()-p.stat().st_mtime)/86400)
    def refresh(self):
        checks=[]
        def add(label,points,maxp,detail):checks.append((label,points,maxp,detail))
        add("README.md",10 if self.present("README.md") else 0,10,"Present" if self.present("README.md") else "Missing")
        add("LICENSE",8 if self.present("LICENSE") else 0,8,"Present" if self.present("LICENSE") else "Missing")
        add("CHANGELOG.md",8 if self.present("CHANGELOG.md") else 0,8,"Present" if self.present("CHANGELOG.md") else "Missing")
        add("SECURITY.md",8 if self.present("SECURITY.md") else 0,8,"Present" if self.present("SECURITY.md") else "Missing")
        add("CONTRIBUTING.md",6 if self.present("CONTRIBUTING.md") else 0,6,"Present" if self.present("CONTRIBUTING.md") else "Missing")
        add("Pull request template",5 if self.present(".github/pull_request_template.md") else 0,5,"Present" if self.present(".github/pull_request_template.md") else "Missing")
        issue_dir=Path(self.repo)/".github"/"ISSUE_TEMPLATE";add("Issue templates",5 if issue_dir.exists() else 0,5,"Present" if issue_dir.exists() else "Missing")
        add("CODEOWNERS",5 if self.present(".github/CODEOWNERS") else 0,5,"Present" if self.present(".github/CODEOWNERS") else "Missing")
        add(".gitignore",5 if self.present(".gitignore") else 0,5,"Present" if self.present(".gitignore") else "Missing")
        add(".gitattributes",5 if self.present(".gitattributes") else 0,5,"Present" if self.present(".gitattributes") else "Missing")
        workflows=Path(self.repo)/".github"/"workflows";add("CI workflows",10 if workflows.exists() and list(workflows.glob("*.y*ml")) else 0,10,"Present" if workflows.exists() and list(workflows.glob("*.y*ml")) else "Missing")
        tests=any((Path(self.repo)/x).exists() for x in ("tests","test","pytest.ini","tox.ini"));add("Tests",10 if tests else 0,10,"Detected" if tests else "Not detected")
        try:
            tags=git(self.repo,"tag","--list");has_tag=tags!="Completed successfully.";add("Version tags",5 if has_tag else 0,5,"Present" if has_tag else "No tags")
        except:add("Version tags",0,5,"Unable to inspect")
        try:
            status=git(self.repo,"status","--porcelain");clean=status=="Completed successfully.";add("Clean working tree",5 if clean else 0,5,"Clean" if clean else "Uncommitted changes")
        except:add("Clean working tree",0,5,"Unable to inspect")
        total=sum(x[1] for x in checks);maximum=sum(x[2] for x in checks);pct=round(total/maximum*100) if maximum else 0
        rating="Excellent" if pct>=90 else "Good" if pct>=75 else "Needs attention" if pct>=55 else "High maintenance risk"
        text=f"REPOSITORY HEALTH SCORE: {pct}/100 - {rating}\n"+"="*78+"\n\n"
        for label,points,maxp,detail in checks:text+=f"[{points:>2}/{maxp:<2}] {label:<28} {detail}\n"
        text+="\nRecommended next actions:\n"
        for label,points,maxp,detail in checks:
            if points<maxp:text+=f"- Improve {label}: {detail}\n"
        self.score.delete("1.0","end");self.score.insert("1.0",text)
        self.refresh_files()
    def refresh_files(self):
        roots=["README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md","CODE_OF_CONDUCT.md",".gitignore",".gitattributes","pyproject.toml","requirements.txt","package.json","Dockerfile",".github/CODEOWNERS",".github/pull_request_template.md"]
        lines=[]
        for rel in roots:
            p=Path(self.repo)/rel
            if p.exists():lines.append(f"PRESENT  {rel:<38} {p.stat().st_size:>10} bytes")
            else:lines.append(f"MISSING  {rel}")
        gh=Path(self.repo)/".github"
        if gh.exists():
            lines.append("\n.github inventory:")
            for p in sorted(gh.rglob("*")):
                if p.is_file():lines.append("  "+str(p.relative_to(self.repo)))
        self.files.delete("1.0","end");self.files.insert("1.0","\n".join(lines))
    def write_template(self,rel,content):
        p=Path(self.repo)/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and not messagebox.askyesno("Replace file",f"{rel} already exists. Replace it?",parent=self):return
        p.write_text(content,encoding="utf-8");messagebox.showinfo("Created",f"Created {rel}. Review and commit it when ready.",parent=self);self.refresh()
    def security_md(self):self.write_template("SECURITY.md","# Security Policy\n\n## Reporting a vulnerability\n\nPlease report suspected vulnerabilities privately to the repository maintainers. Do not open a public issue for an unpatched vulnerability. Include affected versions, reproduction steps, impact, and any proposed remediation.\n\n## Supported versions\n\nThe latest stable release receives security fixes.\n")
    def contributing_md(self):self.write_template("CONTRIBUTING.md","# Contributing\n\n1. Create or link an issue.\n2. Create a focused branch.\n3. Add or update tests and documentation.\n4. Run relevant checks locally.\n5. Open a pull request with a clear summary, validation evidence, and risk notes.\n\nKeep changes small and avoid unrelated formatting changes.\n")
    def issue_templates(self):
        self.write_template(".github/ISSUE_TEMPLATE/bug_report.md","---\nname: Bug report\nabout: Report a reproducible problem\ntitle: '[Bug] '\nlabels: bug\n---\n\n## Description\n\n## Steps to reproduce\n1.\n\n## Expected behavior\n\n## Actual behavior\n\n## Environment\n- OS:\n- Version:\n\n## Logs/screenshots\n")
        self.write_template(".github/ISSUE_TEMPLATE/feature_request.md","---\nname: Feature request\nabout: Suggest an improvement\ntitle: '[Feature] '\nlabels: enhancement\n---\n\n## Problem\n\n## Proposed solution\n\n## Alternatives\n\n## Acceptance criteria\n- [ ]\n")
    def pr_template(self):self.write_template(".github/pull_request_template.md","## Summary\n\n## Changes\n- \n\n## Validation\n- [ ] Tests passed\n- [ ] Documentation updated\n- [ ] Security/release impact reviewed\n\n## Risk and rollback\n\n")
    def codeowners(self):
        owner=simpledialog.askstring("CODEOWNERS","GitHub owner/team, for example @username or @org/team:",parent=self)
        if owner:self.write_template(".github/CODEOWNERS",f"* {owner}\n")
    def gitattributes(self):self.write_template(".gitattributes","* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.jpeg binary\n*.gif binary\n*.zip binary\n*.pdf binary\n")

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
        except Exception as e:messagebox.showerror("Worktrees",str(e),parent=self)
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
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def remove(self):
        s=self.tree.selection()
        if not s:return
        path=self.rows[int(s[0])].get("worktree","")
        if path==str(Path(self.repo).resolve()):return messagebox.showwarning("Worktree","The main worktree cannot be removed here.",parent=self)
        if messagebox.askyesno("Remove worktree",f"Remove worktree?\n{path}",parent=self):
            try:messagebox.showinfo("Worktree",git(self.repo,"worktree","remove",path),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def prune(self):
        try:messagebox.showinfo("Worktree",git(self.repo,"worktree","prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)

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
        except Exception as e:messagebox.showerror("Compare",str(e),parent=self)
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
        except Exception as e:messagebox.showerror("Compare",str(e),parent=self)
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
        except Exception as e:messagebox.showerror("Recovery",str(e),parent=self)
    def checkpoint(self):
        import datetime
        label=simpledialog.askstring("Checkpoint","Optional label:",initialvalue="manual",parent=self) or "manual"
        safe="".join(c if c.isalnum() or c in "-_" else "-" for c in label)
        name=f"gccc-backup/{safe}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:messagebox.showinfo("Checkpoint",git(self.repo,"branch",name),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Checkpoint",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=Path(self.repo).name+"-backup.bundle")
        if p:
            try:messagebox.showinfo("Bundle",git(self.repo,"bundle","create",p,"--all"),parent=self)
            except Exception as e:messagebox.showerror("Bundle",str(e),parent=self)
    def verify(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle"),("All files","*")])
        if p:
            try:messagebox.showinfo("Bundle verification",git(self.repo,"bundle","verify",p),parent=self)
            except Exception as e:messagebox.showerror("Bundle verification",str(e),parent=self)
    def restore_bundle(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle")])
        if not p:return
        parent=filedialog.askdirectory(parent=self,title="Choose folder in which to restore the repository")
        if not parent:return
        name=simpledialog.askstring("Restore","New repository folder name:",initialvalue=Path(self.repo).name+"-recovered",parent=self)
        if name:
            try:messagebox.showinfo("Restore",git(parent,"clone",p,name),parent=self)
            except Exception as e:messagebox.showerror("Restore",str(e),parent=self)

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
                except:remote="-"
                try:ahead=git(p,"rev-list","--count","@{u}..HEAD");behind=git(p,"rev-list","--count","HEAD..@{u}")
                except:ahead=behind="-"
                row={"path":str(p),"branch":branch,"state":state,"ahead":ahead,"behind":behind,"remote":remote};self.rows.append(row)
                self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p.name,branch,state,ahead,behind,remote))
            except Exception:pass
    def selected(self):return [self.rows[int(i)] for i in self.tree.selection()]
    def fetch(self):
        selected=self.selected()
        if not selected:return
        errors=[]
        for r in selected:
            try:git(r["path"],"fetch","--all","--prune")
            except Exception as e:errors.append(f"{Path(r['path']).name}: {e}")
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
        except Exception as e:return False,str(e)
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
                except:v="Not set"
                lines.append(f"  {key}: {v}")
            lines.append("\nRepository integrity\n  "+git(self.repo,"fsck","--no-progress").replace("\n","\n  "))
        except Exception as e:lines.append("Repository diagnostics error: "+str(e))
        self.report="\n".join(lines);self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def copy(self):self.clipboard_clear();self.clipboard_append(getattr(self,"report",""));messagebox.showinfo("Diagnostics","Report copied to clipboard.",parent=self)

class SyncCenter(tk.Toplevel):
    """Safe, guided synchronization for a local repository."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Smart Sync Center");self.geometry("1050x700");self.minsize(900,600);self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Fetch",self.fetch),("Safe sync",self.safe_sync),("Push",self.push_now),("Create checkpoint",self.checkpoint)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def snapshot(self):
        branch=git(self.repo,"branch","--show-current"); status=git(self.repo,"status","--porcelain")
        try:upstream=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}")
        except:upstream=""
        ahead=behind="-"
        if upstream:
            ahead=git(self.repo,"rev-list","--count","@{u}..HEAD");behind=git(self.repo,"rev-list","--count","HEAD..@{u}")
        return branch,status,upstream,ahead,behind
    def refresh(self):
        try:
            branch,status,upstream,ahead,behind=self.snapshot();clean=status=="Completed successfully."
            rec="No action required."
            if not upstream:rec="Set an upstream branch before synchronization."
            elif not clean:rec="Commit or stash local changes before synchronization."
            elif str(behind)!="0" and str(ahead)!="0":rec="Branch has diverged. Compare/review before rebasing or merging."
            elif str(behind)!="0":rec="Remote is ahead. Safe sync can fast-forward pull."
            elif str(ahead)!="0":rec="Local branch is ahead. Push when ready."
            report=f"SMART SYNC\n{'='*72}\nRepository: {self.repo}\nBranch: {branch}\nUpstream: {upstream or 'Not configured'}\nWorking tree: {'Clean' if clean else 'Changed'}\nAhead: {ahead}\nBehind: {behind}\n\nRecommendation: {rec}\n"
            self.text.delete("1.0","end");self.text.insert("1.0",report)
        except Exception as e:messagebox.showerror("Smart Sync",str(e),parent=self)
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def checkpoint(self):
        import datetime
        name=f"gccc-backup/pre-sync-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:git(self.repo,"branch",name);messagebox.showinfo("Checkpoint",f"Created {name}",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Checkpoint",str(e),parent=self)
    def safe_sync(self):
        try:
            git(self.repo,"fetch","--all","--prune")
            branch,status,upstream,ahead,behind=self.snapshot()
            if status!="Completed successfully.":raise GitError("Working tree has local changes. Commit or stash them before sync.")
            if not upstream:raise GitError("No upstream is configured for the current branch.")
            if str(ahead)!="0" and str(behind)!="0":raise GitError("Branch histories have diverged. Use Compare and choose a deliberate merge or rebase workflow.")
            if str(behind)!="0":out=git(self.repo,"pull","--ff-only")
            elif str(ahead)!="0":out="Local commits are ready to push. Safe Sync does not auto-push without confirmation."
            else:out="Already synchronized."
            messagebox.showinfo("Safe Sync",out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Safe Sync",str(e),parent=self)
    def push_now(self):
        if not messagebox.askyesno("Push","Push the current branch to its configured upstream?",parent=self):return
        try:messagebox.showinfo("Push",git(self.repo,"push"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Push",str(e),parent=self)

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
        except Exception as e:self.put("TRACKED TEXT SEARCH",str(e))
    def search_commits(self):
        q=self.q.get().strip()
        if not q:return
        try:self.put("COMMIT MESSAGE SEARCH",git(self.repo,"log","--all","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s","--grep",q,"-i"))
        except Exception as e:self.put("COMMIT MESSAGE SEARCH",str(e))
    def search_files(self):
        q=self.q.get().strip().lower()
        if not q:return
        try:
            files=git(self.repo,"ls-files");matches=[x for x in files.splitlines() if q in x.lower()];self.put("FILE NAME SEARCH","\n".join(matches) if matches else "No tracked filenames matched.")
        except Exception as e:self.put("FILE NAME SEARCH",str(e))

class ChangeReviewCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Pre-Commit Review Center");self.geometry("1160x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.msg=tk.StringVar()
        for t,c in [("Refresh",self.refresh),("Stage selected",self.stage),("Unstage selected",self.unstage),("Commit",self.commit_now)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        ttk.Entry(top,textvariable=self.msg).pack(side="left",fill="x",expand=True,padx=8)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.tree=ttk.Treeview(l,columns=("state","file"),show="headings",selectmode="extended");self.tree.heading("state",text="State");self.tree.heading("file",text="File");self.tree.column("state",width=70);self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.show_diff())
        nb=ttk.Notebook(r);nb.pack(fill="both",expand=True);a=ttk.Frame(nb);b=ttk.Frame(nb);nb.add(a,text="Diff");nb.add(b,text="Checks")
        self.diff=tk.Text(a,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.diff.pack(fill="both",expand=True);self.checks=tk.Text(b,wrap="word",font=("Consolas",9));self.checks.pack(fill="both",expand=True)
    def refresh(self):
        raw=git(self.repo,"status","--porcelain=v1");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if len(line)>3:self.rows.append((line[:2],line[3:]));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
        def chk(*args):
            try:o=git(self.repo,*args);return "PASS" if o=="Completed successfully." else o
            except Exception as e:return str(e)
        large=[]
        for _,f in self.rows:
            p=Path(self.repo)/f
            try:
                if p.is_file() and p.stat().st_size>5*1024*1024:large.append(f"{f} ({p.stat().st_size/1024/1024:.1f} MB)")
            except OSError:pass
        text="PRE-COMMIT CHECKS\n"+"="*70+"\nStaged whitespace: "+chk("diff","--cached","--check")+"\n\nUnstaged whitespace: "+chk("diff","--check")+"\n\nChanged files above 5 MB:\n"+("\n".join(large) or "None")
        self.checks.delete("1.0","end");self.checks.insert("1.0",text)
    def paths(self):return [self.rows[int(i)][1] for i in self.tree.selection()]
    def stage(self):
        p=self.paths()
        if p:git(self.repo,"add","--",*p);self.refresh()
    def unstage(self):
        p=self.paths()
        if p:git(self.repo,"restore","--staged","--",*p);self.refresh()
    def show_diff(self):
        p=self.paths()
        if not p:return
        def d(*args):
            try:o=git(self.repo,*args);return "" if o=="Completed successfully." else o
            except Exception as e:return str(e)
        v="STAGED\n"+"="*60+"\n"+d("diff","--cached","--",p[0])+"\n\nUNSTAGED\n"+"="*60+"\n"+d("diff","--",p[0])
        self.diff.delete("1.0","end");self.diff.insert("1.0",v)
    def commit_now(self):
        m=self.msg.get().strip()
        if not m:return messagebox.showwarning("Commit","Enter a commit message.",parent=self)
        try:
            staged=git(self.repo,"diff","--cached","--name-only")
            if staged=="Completed successfully.":raise GitError("Nothing is staged.")
            if len(m)<8 and not messagebox.askyesno("Short message","Commit message is very short. Continue?",parent=self):return
            messagebox.showinfo("Commit",git(self.repo,"commit","-m",m),parent=self);self.msg.set("");self.refresh()
        except Exception as e:messagebox.showerror("Commit",str(e),parent=self)

class RepositoryNotesCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.path=Path(repo)/".git"/"gccc-notes.md";self.title("Repository Notes");self.geometry("850x620")
        ttk.Label(self,text="Private local notes stored under .git and excluded from normal commits.",padding=8).pack(fill="x");self.text=tk.Text(self,wrap="word",undo=True);self.text.pack(fill="both",expand=True,padx=8);ttk.Button(self,text="Save",command=self.save).pack(anchor="e",padx=8,pady=8)
        self.text.insert("1.0",self.path.read_text(encoding="utf-8",errors="replace") if self.path.exists() else "# Repository Notes\n\n## Current focus\n\n## Decisions\n\n## Follow-ups\n\n## Release reminders\n")
    def save(self):
        self.path.write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Notes","Saved under .git/gccc-notes.md",parent=self)

class BranchCleanupCenter(tk.Toplevel):
    """Safe local branch cleanup with merged/stale awareness."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Branch Cleanup Center");self.geometry("1050x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Delete selected merged",self.delete_selected),("Prune remotes",self.prune),("Open Worktrees",lambda:WorktreeCenter(self,self.repo))]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("branch","merged","age","upstream","worktree"),show="headings",selectmode="extended")
        for c,t,w in [("branch","Branch",260),("merged","Merged",80),("age","Last commit",130),("upstream","Upstream",260),("worktree","Worktree",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Only branches reported merged into the current branch can be deleted from this screen. The current branch and worktree branches are protected.",padding=8).pack(fill="x")
    def refresh(self):
        try:
            current=git(self.repo,"branch","--show-current");merged=set(x.strip().lstrip("* ") for x in git(self.repo,"branch","--merged").splitlines())
            wt=git(self.repo,"worktree","list","--porcelain");used=set()
            for line in wt.splitlines():
                if line.startswith("branch refs/heads/"):used.add(line.replace("branch refs/heads/","",1))
            raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(committerdate:short)%09%(upstream:short)","refs/heads/")
            self.rows=[];self.tree.delete(*self.tree.get_children())
            for line in raw.splitlines():
                p=line.split("\t");b=p[0];row={"branch":b,"merged":b in merged,"date":p[1] if len(p)>1 else "","upstream":p[2] if len(p)>2 else "","used":b in used,"current":b==current};self.rows.append(row)
                self.tree.insert("","end",iid=str(len(self.rows)-1),values=(b,"Yes" if row["merged"] else "No",row["date"],row["upstream"] or "-","Yes" if row["used"] else "No"))
        except Exception as e:messagebox.showerror("Branch Cleanup",str(e),parent=self)
    def delete_selected(self):
        selected=[self.rows[int(i)] for i in self.tree.selection()]
        eligible=[r for r in selected if r["merged"] and not r["current"] and not r["used"]]
        if not eligible:return messagebox.showinfo("Branch Cleanup","No selected branches are safely eligible for deletion.",parent=self)
        names="\n".join(r["branch"] for r in eligible)
        if messagebox.askyesno("Delete merged branches",f"Delete these local merged branches?\n\n{names}",parent=self):
            errors=[]
            for r in eligible:
                try:git(self.repo,"branch","-d",r["branch"])
                except Exception as e:errors.append(f"{r['branch']}: {e}")
            self.refresh();messagebox.showinfo("Branch Cleanup","Completed." if not errors else "Some branches were not deleted:\n"+"\n".join(errors),parent=self)
    def prune(self):
        try:messagebox.showinfo("Prune",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Prune",str(e),parent=self)

class ProjectSnapshotCenter(tk.Toplevel):
    """Generate a compact local repository handover snapshot."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Project Snapshot");self.geometry("1050x720");self._build();self.generate()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Regenerate",command=self.generate).pack(side="left");ttk.Button(top,text="Export Markdown",command=self.export).pack(side="left",padx=3);ttk.Button(top,text="Copy",command=self.copy).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except Exception as e:return "Unavailable: "+str(e)
    def generate(self):
        branch=self.safe("branch","--show-current");status=self.safe("status","--short","--branch");recent=self.safe("log","-10","--date=short","--pretty=format:- %h %ad %an: %s");tags=self.safe("tag","--sort=-creatordate");remotes=self.safe("remote","-v")
        notes=Path(self.repo)/".git"/"gccc-notes.md";note_text=notes.read_text(encoding="utf-8",errors="replace") if notes.exists() else "No private repository notes."
        key=[]
        for f in ("README.md","CHANGELOG.md","RELEASE_NOTES.md","USER_GUIDE.md","SECURITY.md","CONTRIBUTING.md"):
            if (Path(self.repo)/f).exists():key.append(f)
        self.snapshot=f"# Project Snapshot: {Path(self.repo).name}\n\n## Repository\n- Path: `{self.repo}`\n- Current branch: `{branch}`\n- Key docs: {', '.join(key) or 'None detected'}\n\n## Working tree\n```text\n{status}\n```\n\n## Recent commits\n{recent}\n\n## Recent tags\n```text\n{tags}\n```\n\n## Remotes\n```text\n{remotes}\n```\n\n## Private local notes\n{note_text}\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.snapshot)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=f"{Path(self.repo).name}-snapshot.md")
        if p:Path(p).write_text(self.snapshot,encoding="utf-8");messagebox.showinfo("Snapshot",f"Saved {p}",parent=self)
    def copy(self):self.clipboard_clear();self.clipboard_append(self.snapshot);messagebox.showinfo("Snapshot","Copied to clipboard.",parent=self)

class PatchCenter(tk.Toplevel):
    """Create, inspect, validate and apply Git patch files without leaving the GUI."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Patch Center");self.geometry("1100x740");self.minsize(900,620);self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Export working diff",self.export_working),("Export staged diff",self.export_staged),("Create patch series",self.format_patch),("Inspect patch",self.inspect_patch),("Apply patch",self.apply_patch),("Apply mailbox",self.apply_mailbox)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.text.insert("1.0","Patch Center\n\nExport normal or staged changes as .patch files, create a format-patch series from commits, inspect/check a patch before applying it, or apply email-style patches with git am.\n")
    def save_diff(self,staged):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".patch",initialfile="staged.patch" if staged else "working-tree.patch",filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            args=["diff"]+(["--cached"] if staged else []);out=git(self.repo,*args)
            if out=="Completed successfully.":return messagebox.showinfo("Patch","There are no changes to export.",parent=self)
            Path(p).write_text(out+"\n",encoding="utf-8");messagebox.showinfo("Patch",f"Saved {p}",parent=self)
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def export_working(self):self.save_diff(False)
    def export_staged(self):self.save_diff(True)
    def format_patch(self):
        base=simpledialog.askstring("Patch series","Base ref, e.g. main or v1.3.0:",initialvalue="main",parent=self)
        if not base:return
        folder=filedialog.askdirectory(parent=self,title="Choose output folder")
        if folder:
            try:messagebox.showinfo("Patch series",git(self.repo,"format-patch","-o",folder,f"{base}..HEAD"),parent=self)
            except Exception as e:messagebox.showerror("Patch series",str(e),parent=self)
    def inspect_patch(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            content=Path(p).read_text(encoding="utf-8",errors="replace");check=""
            try:check=git(self.repo,"apply","--check",p)
            except Exception as e:check=str(e)
            self.text.delete("1.0","end");self.text.insert("1.0",f"APPLY CHECK\n{'='*72}\n{check}\n\nPATCH CONTENT\n{'='*72}\n{content}")
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def apply_patch(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            git(self.repo,"apply","--check",p)
            if messagebox.askyesno("Apply patch",f"Patch check passed. Apply?\n{p}",parent=self):messagebox.showinfo("Patch",git(self.repo,"apply",p),parent=self)
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def apply_mailbox(self):
        files=filedialog.askopenfilenames(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if files and messagebox.askyesno("Apply mailbox",f"Apply {len(files)} patch(es) as commits using git am?",parent=self):
            try:messagebox.showinfo("Mailbox",git(self.repo,"am",*files),parent=self)
            except Exception as e:messagebox.showerror("Mailbox",str(e)+"\n\nResolve conflicts then run git am --continue, or abort with git am --abort.",parent=self)

class BisectCenter(tk.Toplevel):
    """Guided Git bisect for finding the commit that introduced a regression."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Regression Finder - Git Bisect");self.geometry("1000x680");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        self.good=tk.StringVar();self.bad=tk.StringVar(value="HEAD")
        ttk.Label(top,text="Known good ref").pack(side="left");ttk.Entry(top,textvariable=self.good,width=22).pack(side="left",padx=3);ttk.Label(top,text="Known bad ref").pack(side="left");ttk.Entry(top,textvariable=self.bad,width=22).pack(side="left",padx=3)
        for t,c in [("Start",self.start),("Mark good",lambda:self.mark("good")),("Mark bad",lambda:self.mark("bad")),("Skip",lambda:self.mark("skip")),("Reset",self.reset)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def status(self):
        try:return git(self.repo,"status","--short","--branch")+"\n\nCurrent commit:\n"+git(self.repo,"show","-s","--date=short","--pretty=format:%H%n%ad%n%an%n%s","HEAD")
        except Exception as e:return str(e)
    def refresh(self):self.text.delete("1.0","end");self.text.insert("1.0","GIT BISECT\n"+"="*72+"\n\n"+self.status()+"\n\nWorkflow: start with a known good and bad ref, test the checked-out revision, then mark it Good, Bad, or Skip. Git narrows the regression to one commit.")
    def clean(self):
        s=git(self.repo,"status","--porcelain");return s=="Completed successfully."
    def start(self):
        if not self.clean():return messagebox.showwarning("Bisect","Commit or stash changes before starting bisect.",parent=self)
        g=self.good.get().strip();b=self.bad.get().strip()
        if not g or not b:return messagebox.showwarning("Bisect","Enter known good and bad refs.",parent=self)
        try:git(self.repo,"bisect","start",b,g);self.refresh()
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
    def mark(self,state):
        try:out=git(self.repo,"bisect",state);self.refresh();messagebox.showinfo("Bisect",out,parent=self)
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
    def reset(self):
        try:messagebox.showinfo("Bisect",git(self.repo,"bisect","reset"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
