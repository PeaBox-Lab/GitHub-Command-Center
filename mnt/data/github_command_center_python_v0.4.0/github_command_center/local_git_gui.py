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
        for t,c in [("Diff",self.diff),("Visual history",lambda:CommitGraphWindow(self,self.repo)),("Resolve conflicts",lambda:ConflictResolver(self,self.repo)),("Advanced",lambda:AdvancedGitWindow(self,self.repo)),("Discard",self.discard),("Clean preview",self.clean),("Open folder",self.open_folder)]:ttk.Button(foot,text=t,command=c).pack(side="left",padx=2)
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
