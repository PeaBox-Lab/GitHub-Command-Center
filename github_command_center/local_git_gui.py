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
        for t,c in [("Diff",self.diff),("Visual history",lambda:CommitGraphWindow(self,self.repo)),("Resolve conflicts",lambda:ConflictResolver(self,self.repo)),("Advanced",lambda:AdvancedGitWindow(self,self.repo)),("Release Center",lambda:ReleaseCenter(self,self.repo)),("Pull Requests",lambda:PullRequestCenter(self,self.repo)),("Actions",lambda:ActionsCenter(self,self.repo)),("Security",lambda:SecurityCenter(self,self.repo)),("Health",lambda:RepositoryHealthCenter(self,self.repo)),("Worktrees",lambda:WorktreeCenter(self,self.repo)),("Discard",self.discard),("Clean preview",self.clean),("Open folder",self.open_folder)]:ttk.Button(foot,text=t,command=c).pack(side="left",padx=2)
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
