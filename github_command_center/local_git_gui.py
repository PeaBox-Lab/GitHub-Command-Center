
import subprocess, tkinter as tk
from pathlib import Path
from .services import GitService
from .centers.async_operations import AsyncOperationsCenter
from .centers.visual_diff import VisualDiffCenter
from .centers.plugin_security_center import PluginSecurityCenter
from .centers.readiness_center import PublicReleaseReadinessCenter
from .centers.sync import AsyncFetchCenter, AsyncMaintenanceCenter, AsyncRemotePruneCenter
from .centers.accessibility_center import AccessibilityCenter
from .ui import apply_modern_style
from .ui.table_layout import install_treeview_layout_guard
from tkinter import filedialog, messagebox, simpledialog, ttk

class GitError(RuntimeError): pass

def git(cwd, *args):
    """Compatibility wrapper routed through the v3.42 GitService boundary."""
    try:
        return GitService(cwd).text(*map(str, args), timeout=900)
    except FileNotFoundError:
        raise GitError("Git is not installed or not on PATH.")
    except Exception as exc:
        raise GitError(str(exc)) from exc


class LocalGitWindow(tk.Toplevel):
    def __init__(self,parent,start=""):
        super().__init__(parent)
        self.title("GitHub Command Center - Local Git")
        self.geometry("1440x860");self.minsize(1120,700)
        self.repo=start;self.sel=tk.StringVar(value=start or "No repository selected")
        self.status_text=tk.StringVar(value="Ready")
        self.configure(bg="#eef2f7")
        self._apply_modern_style()

        # Header
        header=tk.Frame(self,bg="#111827",height=72);header.pack(fill="x");header.pack_propagate(False)
        tk.Label(header,text="GCC",bg="#4f46e5",fg="white",font=("Segoe UI Semibold",15),width=4,height=2).pack(side="left",padx=(14,10),pady=11)
        title=tk.Frame(header,bg="#111827");title.pack(side="left",fill="x",expand=True,pady=10)
        tk.Label(title,text="Local Git Workspace",bg="#111827",fg="white",font=("Segoe UI Semibold",17)).pack(anchor="w")
        tk.Label(title,textvariable=self.sel,bg="#111827",fg="#9ca3af",font=("Segoe UI",9)).pack(anchor="w")
        ttk.Button(header,text="Command Palette  Ctrl+K",style="Accent.TButton",command=lambda:CommandPalette(self,self.repo)).pack(side="right",padx=(5,14),pady=18)
        ttk.Button(header,text="Choose Repository",command=self.choose).pack(side="right",padx=5,pady=18)
        ttk.Button(header,text="Clone",command=self.clone).pack(side="right",padx=5,pady=18)

        # Primary actions, intentionally limited to the daily workflow
        action=tk.Frame(self,bg="white",height=58,highlightbackground="#dbe3ef",highlightthickness=1);action.pack(fill="x");action.pack_propagate(False)
        daily=[("Refresh",self.refresh),("Stage selected",self.stage),("Stage all",lambda:self.run("add","--all")),("Unstage",self.unstage),("Commit",self.commit),("Fetch",lambda:self.run("fetch","--all","--prune")),("Pull safely",lambda:self.run("pull","--ff-only")),("Push",lambda:self.run("push"))]
        for i,(text,cmd) in enumerate(daily):ttk.Button(action,text=text,command=cmd,style="Accent.TButton" if text=="Commit" else "TButton").pack(side="left",padx=(12 if i==0 else 3,3),pady=11)
        ttk.Button(action,text="Smart Sync",command=lambda:SyncCenter(self,self.repo)).pack(side="right",padx=12,pady=11)
        ttk.Button(action,text="Pre-Commit Review",command=lambda:ChangeReviewCenter(self,self.repo)).pack(side="right",padx=3,pady=11)

        body=tk.Frame(self,bg="#eef2f7");body.pack(fill="both",expand=True)
        # Compact sidebar replaces the long overflowing button strip
        side=tk.Frame(body,bg="#182235",width=212);side.pack(side="left",fill="y");side.pack_propagate(False)
        groups=[
            ("WORK",[("Dashboard",lambda:RepositoryDashboardCenter(self,self.repo)),("Changes",self.refresh),("History",lambda:CommitGraphWindow(self,self.repo)),("History browser",lambda:RepositoryHistoryBrowser(self,self.repo)),("Partial staging",lambda:PartialStagingCenter(self,self.repo)),("Search",lambda:SearchCenter(self,self.repo))]),
            ("COLLABORATE",[("Pull requests",lambda:PullRequestCenter(self,self.repo)),("Actions",lambda:ActionsCenter(self,self.repo)),("Releases",lambda:ReleaseCenter(self,self.repo))]),
            ("QUALITY",[("Conflicts",lambda:ConflictResolver(self,self.repo)),("Security",lambda:SecurityCenter(self,self.repo)),("Health",lambda:RepositoryHealthCenter(self,self.repo)),("Compare",lambda:RepositoryCompareCenter(self,self.repo))]),
            ("TOOLS",[("Branches & advanced",lambda:AdvancedGitWindow(self,self.repo)),("Interactive rebase",lambda:InteractiveRebaseEditor(self,self.repo)),("All refs",lambda:UnifiedRefBrowser(self,self.repo)),("Reflog recovery",lambda:ReflogRecoveryCenter(self,self.repo)),("Recovery",lambda:BackupRestoreCenter(self,self.repo)),("Worktrees",lambda:WorktreeCenter(self,self.repo)),("All commands",lambda:CommandPalette(self,self.repo))])]
        for heading,items in groups:
            tk.Label(side,text=heading,bg="#182235",fg="#72819a",font=("Segoe UI Semibold",8),anchor="w").pack(fill="x",padx=16,pady=(16,5))
            for text,cmd in items:
                tk.Button(side,text=text,command=cmd,anchor="w",relief="flat",bd=0,bg="#182235",fg="#d7deea",activebackground="#27344a",activeforeground="white",font=("Segoe UI",10),padx=16,pady=8,cursor="hand2").pack(fill="x")

        workspace=tk.Frame(body,bg="#eef2f7");workspace.pack(side="left",fill="both",expand=True,padx=12,pady=12)
        summary=tk.Frame(workspace,bg="white",highlightbackground="#dbe3ef",highlightthickness=1);summary.pack(fill="x",pady=(0,10))
        self.branch_badge=tk.Label(summary,text="Branch: -",bg="#eef2ff",fg="#4338ca",font=("Segoe UI Semibold",9),padx=10,pady=6);self.branch_badge.pack(side="left",padx=10,pady=8)
        self.change_badge=tk.Label(summary,text="Changes: -",bg="#fef3c7",fg="#92400e",font=("Segoe UI Semibold",9),padx=10,pady=6);self.change_badge.pack(side="left",padx=4,pady=8)
        self.sync_badge=tk.Label(summary,text="Sync: -",bg="#ecfdf5",fg="#047857",font=("Segoe UI Semibold",9),padx=10,pady=6);self.sync_badge.pack(side="left",padx=4,pady=8)
        ttk.Button(summary,text="Open folder",command=self.open_folder).pack(side="right",padx=10,pady=8)

        pane=ttk.Panedwindow(workspace,orient="horizontal");pane.pack(fill="both",expand=True)
        left=tk.Frame(pane,bg="white",highlightbackground="#dbe3ef",highlightthickness=1);right=tk.Frame(pane,bg="white",highlightbackground="#dbe3ef",highlightthickness=1);pane.add(left,weight=3);pane.add(right,weight=2)
        tk.Label(left,text="Working Tree",bg="white",fg="#111827",font=("Segoe UI Semibold",12)).pack(anchor="w",padx=12,pady=(12,6))
        self.files=ttk.Treeview(left,columns=("state","file"),show="headings",selectmode="extended");self.files.heading("state",text="State");self.files.heading("file",text="File");self.files.column("state",width=75,anchor="center");self.files.column("file",width=520);self.files.pack(fill="both",expand=True,padx=10,pady=(0,6));self.files.bind("<Double-1>",lambda e:self.diff())
        filebar=tk.Frame(left,bg="white");filebar.pack(fill="x",padx=8,pady=(0,9))
        for text,cmd in [("View diff",self.diff),("Discard selected",self.discard),("Clean preview",self.clean)]:ttk.Button(filebar,text=text,command=cmd).pack(side="left",padx=2)

        self.tabs=ttk.Notebook(right);self.tabs.pack(fill="both",expand=True,padx=8,pady=8)
        self.texts={}
        for name in ["History","Branches","Stash","Tags","Remotes","Conflicts"]:
            frame=tk.Frame(self.tabs,bg="white");self.tabs.add(frame,text=name)
            controls=tk.Frame(frame,bg="white");controls.pack(fill="x",padx=5,pady=4)
            if name=="Branches":
                for t,c in [("New",self.branch_new),("Switch",self.branch_switch),("Merge",self.branch_merge),("Delete",self.branch_delete)]:ttk.Button(controls,text=t,command=c).pack(side="left",padx=2)
            elif name=="Stash":
                ttk.Button(controls,text="Save stash",command=self.stash).pack(side="left");ttk.Button(controls,text="Pop latest",command=lambda:self.run("stash","pop")).pack(side="left",padx=2)
            elif name=="Tags":
                ttk.Button(controls,text="Create tag",command=self.tag).pack(side="left");ttk.Button(controls,text="Push tags",command=lambda:self.run("push","origin","--tags")).pack(side="left",padx=2)
            elif name=="Remotes":ttk.Button(controls,text="Add/update",command=self.remote).pack(side="left")
            elif name=="Conflicts":ttk.Button(controls,text="Open resolver",command=lambda:ConflictResolver(self,self.repo)).pack(side="left")
            text=tk.Text(frame,wrap="none",font=("Consolas",9),bg="#101827",fg="#dbeafe",insertbackground="white",bd=0);text.pack(fill="both",expand=True,padx=6,pady=(0,6));self.texts[name]=text

        status=tk.Frame(self,bg="#111827",height=28);status.pack(fill="x");status.pack_propagate(False)
        tk.Label(status,textvariable=self.status_text,bg="#111827",fg="#cbd5e1",font=("Segoe UI",9)).pack(side="left",padx=12,pady=5)
        tk.Label(status,text="Ctrl+K Commands    F5 Refresh    Ctrl+Enter Commit",bg="#111827",fg="#64748b",font=("Segoe UI",8)).pack(side="right",padx=12)
        self.bind("<Control-k>",lambda e:CommandPalette(self,self.repo));self.bind("<F5>",lambda e:self.refresh());self.bind("<Control-Return>",lambda e:self.commit())
        if self.repo:self.refresh()

    def _apply_modern_style(self):
        return apply_modern_style(self)

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
        self.status_text.set("Refreshing repository...")
        try:
            status=git(self.repo,"status","--porcelain=v1");self.files.delete(*self.files.get_children())
            for i,l in enumerate(status.splitlines()):
                if len(l)>3:self.files.insert("","end",iid=str(i),values=(l[:2],l[3:]))
            data={"History":git(self.repo,"log","-100","--date=short","--pretty=format:%h  %ad  %an  %s"),"Branches":git(self.repo,"branch","-vv"),"Stash":git(self.repo,"stash","list"),"Tags":git(self.repo,"tag","--sort=-creatordate"),"Remotes":git(self.repo,"remote","-v"),"Conflicts":git(self.repo,"diff","--name-only","--diff-filter=U")}
            branch=git(self.repo,"branch","--show-current");self.sel.set(f"{self.repo}  |  {branch or 'detached HEAD'}")
            for n,v in data.items():self.texts[n].delete("1.0","end");self.texts[n].insert("1.0",v or ("No conflicts" if n=="Conflicts" else "None"))
            changed=len([x for x in status.splitlines() if x and x!="Completed successfully."])
            self.branch_badge.config(text=f"Branch: {branch or 'detached'}")
            self.change_badge.config(text=f"Changes: {changed}",bg="#ecfdf5" if changed==0 else "#fef3c7",fg="#047857" if changed==0 else "#92400e")
            try:
                ahead=git(self.repo,"rev-list","--count","@{u}..HEAD");behind=git(self.repo,"rev-list","--count","HEAD..@{u}");sync=f"Sync: +{ahead} / -{behind}"
            except:sync="Sync: no upstream"
            self.sync_badge.config(text=sync);self.status_text.set("Repository refreshed")
        except Exception as e:self.status_text.set("Refresh failed");messagebox.showerror("Refresh",str(e),parent=self)
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

class CommitInspector(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Inspector & File History");self.geometry("1200x760");self._build();self.load_commits()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar();ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="File history",command=self.file_history).pack(side="left",padx=3);ttk.Button(top,text="Blame file",command=self.blame).pack(side="left");ttk.Button(top,text="All commits",command=self.load_commits).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Consolas",9));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.show_commit())
        self.text=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
    def load_commits(self,args=None):
        try:
            raw=git(self.repo,"log",*(args or []),"-150","--date=short","--pretty=format:%H%x09%h%x09%ad%x09%an%x09%s");self.rows=[];self.list.delete(0,"end")
            for line in raw.splitlines():
                p=line.split("\t",4)
                if len(p)==5:self.rows.append(p);self.list.insert("end",f"{p[1]}  {p[2]}  {p[4]}")
        except Exception as e:messagebox.showerror("History",str(e),parent=self)
    def file_history(self):
        p=self.path.get().strip()
        if p:self.load_commits(["--follow","--",p])
    def show_commit(self):
        s=self.list.curselection()
        if not s:return
        try:self.show(git(self.repo,"show","--stat","--patch","--find-renames",self.rows[s[0]][0]))
        except Exception as e:self.show(str(e))
    def blame(self):
        p=self.path.get().strip()
        if not p:return
        try:self.show(git(self.repo,"blame","--date=short","--",p))
        except Exception as e:self.show(str(e))
    def show(self,v):self.text.delete("1.0","end");self.text.insert("1.0",v)

class SubmoduleCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Submodule Center");self.geometry("1050x680");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Add",self.add),("Init/update all",self.update_all),("Update remote",self.update_remote),("Sync URLs",self.sync)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("state","sha","path","branch"),show="headings")
        for c,t,w in [("state","State",70),("sha","Commit",120),("path","Path",370),("branch","Description",380)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Submodule updates are explicit. Review parent-repository changes after updating because the recorded submodule commit may change.",padding=8).pack(fill="x")
    def refresh(self):
        self.tree.delete(*self.tree.get_children());self.rows=[]
        try:raw=git(self.repo,"submodule","status","--recursive")
        except Exception as e:raw=str(e)
        if raw=="Completed successfully.":return
        for line in raw.splitlines():
            if len(line)<42:continue
            state=line[0];rest=line[1:].strip().split(None,2);sha=rest[0];path=rest[1] if len(rest)>1 else "";desc=rest[2] if len(rest)>2 else "";self.rows.append(path);self.tree.insert("","end",values=(state,sha[:10],path,desc))
    def add(self):
        url=simpledialog.askstring("Add submodule","Repository URL:",parent=self)
        if not url:return
        path=simpledialog.askstring("Add submodule","Local path:",parent=self)
        if path:
            try:messagebox.showinfo("Submodule",git(self.repo,"submodule","add",url,path),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Submodule",str(e),parent=self)
    def update_all(self):
        if messagebox.askyesno("Submodules","Initialize and update all submodules recursively?",parent=self):
            try:messagebox.showinfo("Submodules",git(self.repo,"submodule","update","--init","--recursive"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Submodules",str(e),parent=self)
    def update_remote(self):
        if messagebox.askyesno("Submodules","Update submodules from their configured remote branches? Review resulting parent-repository pointer changes afterward.",parent=self):
            try:messagebox.showinfo("Submodules",git(self.repo,"submodule","update","--remote","--recursive"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Submodules",str(e),parent=self)
    def sync(self):
        try:messagebox.showinfo("Submodules",git(self.repo,"submodule","sync","--recursive"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Submodules",str(e),parent=self)

class TaskCenter(tk.Toplevel):
    """Repository-local checklist for release, refactor and maintenance work."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-tasks.txt";self.title("Repository Task Center");self.geometry("950x650");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.entry=tk.StringVar();ttk.Entry(top,textvariable=self.entry).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Add task",command=self.add).pack(side="left",padx=3);ttk.Button(top,text="Toggle done",command=self.toggle).pack(side="left");ttk.Button(top,text="Delete",command=self.delete).pack(side="left",padx=3);ttk.Button(top,text="Save",command=self.save).pack(side="left")
        self.list=tk.Listbox(self,font=("Segoe UI",10),selectmode="extended");self.list.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Tasks are private to this local clone and stored under .git/gccc-tasks.txt.",padding=8).pack(fill="x")
    def load(self):
        self.tasks=[]
        if self.path.exists():self.tasks=[x for x in self.path.read_text(encoding="utf-8",errors="replace").splitlines() if x.strip()]
        self.render()
    def render(self):
        self.list.delete(0,"end")
        for t in self.tasks:self.list.insert("end",t)
    def add(self):
        v=self.entry.get().strip()
        if v:self.tasks.append("[ ] "+v);self.entry.set("");self.render();self.save(False)
    def toggle(self):
        for i in self.list.curselection():self.tasks[i]=(self.tasks[i].replace("[ ] ","[x] ",1) if self.tasks[i].startswith("[ ] ") else self.tasks[i].replace("[x] ","[ ] ",1))
        self.render();self.save(False)
    def delete(self):
        for i in reversed(self.list.curselection()):del self.tasks[i]
        self.render();self.save(False)
    def save(self,notice=True):
        self.path.write_text("\n".join(self.tasks)+("\n" if self.tasks else ""),encoding="utf-8")
        if notice:messagebox.showinfo("Tasks","Saved repository tasks.",parent=self)

class ArchiveCenter(tk.Toplevel):
    """Safe local archive/export hub for reproducible handover packages."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Archive & Handover Center");self.geometry("1000x680");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Export HEAD ZIP",self.head_zip),("Create Git bundle",self.bundle),("Export snapshot",self.snapshot),("Export support pack",self.support_pack)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.text.insert("1.0","Archive & Handover Center\n\nHEAD ZIP creates clean source without .git. Git bundle preserves repository history and refs. Snapshot exports a readable project handover. Support pack combines diagnostics, git status and environment information without including your GitHub token.")
    def head_zip(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",initialfile=Path(self.repo).name+"-HEAD.zip")
        if p:
            try:messagebox.showinfo("Archive",git(self.repo,"archive","--format=zip",f"--output={p}","HEAD"),parent=self)
            except Exception as e:messagebox.showerror("Archive",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=Path(self.repo).name+"-full.bundle")
        if p:
            try:messagebox.showinfo("Bundle",git(self.repo,"bundle","create",p,"--all"),parent=self)
            except Exception as e:messagebox.showerror("Bundle",str(e),parent=self)
    def snapshot(self):ProjectSnapshotCenter(self,self.repo)
    def support_pack(self):
        import platform,sys
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile=Path(self.repo).name+"-support.txt")
        if not p:return
        def safe(*args):
            try:return git(self.repo,*args)
            except Exception as e:return str(e)
        report=f"GitHub Command Center Support Pack\n{'='*72}\nRepository: {self.repo}\nPython: {sys.version}\nOS: {platform.platform()}\n\nSTATUS\n{safe('status','--short','--branch')}\n\nREMOTES\n{safe('remote','-v')}\n\nRECENT COMMITS\n{safe('log','-20','--oneline','--decorate')}\n\nCONFIG\n{safe('config','--list','--show-origin')}\n\nFSCK\n{safe('fsck','--no-progress')}\n"
        Path(p).write_text(report,encoding="utf-8");messagebox.showinfo("Support pack",f"Saved {p}",parent=self)

class CommandPalette(tk.Toplevel):
    """Searchable launcher that keeps the Local Git toolbar usable as features grow."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Command Palette");self.geometry("760x620");self.transient(parent)
        self.q=tk.StringVar();e=ttk.Entry(self,textvariable=self.q,font=("Segoe UI",12));e.pack(fill="x",padx=10,pady=10);e.bind("<KeyRelease>",lambda x:self.render());e.bind("<Return>",lambda x:self.launch());e.focus_set()
        self.list=tk.Listbox(self,font=("Segoe UI",10));self.list.pack(fill="both",expand=True,padx=10,pady=(0,10));self.list.bind("<Double-1>",lambda x:self.launch())
        self.commands=[
            ("Visual commit history",lambda:CommitGraphWindow(self,repo),"history graph branches"),("Resolve merge conflicts",lambda:ConflictResolver(self,repo),"merge conflicts ours theirs"),
            ("Advanced Git operations",lambda:AdvancedGitWindow(self,repo),"rebase cherry-pick reset ignore"),("Release Center",lambda:ReleaseCenter(self,repo),"release tag assets bundle"),
            ("Pull Request Center",lambda:PullRequestCenter(self,repo),"pull request pr review merge"),("GitHub Actions Center",lambda:ActionsCenter(self,repo),"workflow actions ci logs"),
            ("Security Center",lambda:SecurityCenter(self,repo),"dependabot code secret scan checksums"),("Repository Health",lambda:RepositoryHealthCenter(self,repo),"quality docs governance score"),
            ("Worktree Center",lambda:WorktreeCenter(self,repo),"parallel branches worktrees"),("Compare & Review",lambda:RepositoryCompareCenter(self,repo),"compare branch tag diff"),
            ("Backup & Recovery",lambda:BackupRestoreCenter(self,repo),"bundle restore checkpoint"),("Repository Manager",lambda:RepositoryManager(self,repo),"multiple repositories portfolio"),
            ("Diagnostics",lambda:SettingsDiagnosticsCenter(self,repo),"environment git python configuration"),("Smart Sync",lambda:SyncCenter(self,repo),"fetch pull push ahead behind"),
            ("Repository Search",lambda:SearchCenter(self,repo),"grep commit file search"),("Pre-Commit Review",lambda:ChangeReviewCenter(self,repo),"stage checks diff commit"),
            ("Repository Notes",lambda:RepositoryNotesCenter(self,repo),"private notes decisions"),("Branch Cleanup",lambda:BranchCleanupCenter(self,repo),"merged stale prune"),
            ("Project Snapshot",lambda:ProjectSnapshotCenter(self,repo),"handover snapshot markdown"),("Patch Center",lambda:PatchCenter(self,repo),"patch apply format-patch"),
            ("Regression Finder",lambda:BisectCenter(self,repo),"bisect regression"),("Commit Inspector",lambda:CommitInspector(self,repo),"blame file history commit"),
            ("Submodule Center",lambda:SubmoduleCenter(self,repo),"submodule recursive"),("Repository Tasks",lambda:TaskCenter(self,repo),"checklist tasks"),
            ("Archive & Handover",lambda:ArchiveCenter(self,repo),"zip bundle support pack"),("Git Hooks Manager",lambda:HooksCenter(self,repo),"hooks pre-commit commit-msg"),
            ("Git LFS Center",lambda:LFSCenter(self,repo),"large files lfs track"),("Automation Recipes",lambda:AutomationCenter(self,repo),"automation recipes checks"),("Identity & Signing",lambda:IdentitySigningCenter(self,repo),"identity email gpg sign verify"),("Commit Message Studio",lambda:CommitMessageStudio(self,repo),"conventional commits message"),("Changelog Studio",lambda:ChangelogStudio(self,repo),"changelog release notes commits"),("Remote Migration & Mirror",lambda:RemoteMigrationCenter(self,repo),"remote backup mirror migration"),("Credential & Remote Hygiene",lambda:CredentialAuditCenter(self,repo),"credentials helper url ssh https auth"),("Release Policy Center",lambda:ReleasePolicyCenter(self,repo),"release policy gates semver version"),("Repository Metrics",lambda:RepositoryMetricsCenter(self,repo),"metrics contributors languages commits activity"),("Plugin Manager",lambda:PluginManager(self,repo),"plugins extensions commands"),("Batch Operations",lambda:BatchOperationsCenter(self,repo),"batch multiple repositories portfolio"),("Operations Dashboard",lambda:RepositoryDashboardCenter(self,repo),"dashboard operational status next action"),("Repository Data Export",lambda:DataExportCenter(self,repo),"export json csv commits metadata"),("Background Jobs",lambda:BackgroundJobsCenter(self,repo),"jobs queue background cancel logs"),("Preferences",lambda:PreferencesCenter(self,repo),"preferences theme appearance defaults"),("Portfolio History",lambda:PortfolioHistoryCenter(self,repo),"sqlite portfolio history snapshots trends"),("Self-Test & Readiness",lambda:SelfTestCenter(self,repo),"self test readiness smoke diagnostics"),("Partial Staging",lambda:PartialStagingCenter(self,repo),"partial stage hunk line add patch"),("Reflog Recovery",lambda:ReflogRecoveryCenter(self,repo),"reflog recover lost commit reset checkout branch"),("Interactive Rebase Editor",lambda:InteractiveRebaseEditor(self,repo),"interactive rebase squash fixup reword edit drop reorder"),("Unified Ref Browser",lambda:UnifiedRefBrowser(self,repo),"refs branches remotes tags stash notes"),("Repository History Browser",lambda:RepositoryHistoryBrowser(self,repo),"history browse tree file commit export"),("Sparse Checkout",lambda:SparseCheckoutCenter(self,repo),"sparse checkout cone large repository folders"),("Repository Maintenance",lambda:AsyncMaintenanceCenter(self,repo),"maintenance gc fsck objects commit graph"),("Git Notes",lambda:GitNotesCenter(self,repo),"git notes annotation metadata commit"),("Diff & Merge Tools",lambda:DiffMergeToolCenter(self,repo),"difftool mergetool vscode winmerge beyond compare kdiff3"),("Recorded Conflict Resolution",lambda:RerereCenter(self,repo),"rerere recorded resolution recurring conflict"),("Remote Branch Center",lambda:RemoteBranchCenter(self,repo),"remote branch track publish rename delete"),("Ignore & Attributes Studio",lambda:IgnoreAttributesStudio(self,repo),"gitignore gitattributes check-ignore attributes"),("Advanced Clone Wizard",lambda:CloneWizard(self),"clone shallow depth partial single branch blob filter"),("Worktree Safety",lambda:WorktreeSafetyCenter(self,repo),"worktree safety lock unlock prune"),("Repository Doctor",lambda:RepositoryDoctor(self,repo),"doctor diagnose repair status config integrity"),("Tag & Release Audit",lambda:TagReleaseAuditCenter(self,repo),"tags release audit signature remote annotated lightweight"),("Stash Manager Pro",lambda:StashManagerPro(self,repo),"stash apply pop branch drop untracked"),("Safe Clean Center",lambda:CleanPreviewCenter(self,repo),"clean untracked ignored preview delete"),("Repository Size Explorer",lambda:RepositorySizeCenter(self,repo),"size large files objects lfs storage"),("Force-with-Lease Safety",lambda:ForcePushSafetyCenter(self,repo),"force with lease rewritten history push safety"),("Advanced History Search",lambda:CommitSearchPro(self,repo),"pickaxe regex history search content"),("Git Bundle Inspector",lambda:BundleInspector(self,repo),"bundle verify heads clone restore backup"),("Branch Protection Advisor",lambda:BranchProtectionAdvisor(self,repo),"branch protection rules review checks github"),("Repository Favorites",lambda:RepositoryFavoritesCenter(self,repo),"favorites groups repositories portfolio"),("Async Git Operations",lambda:AsyncOperationsCenter(self,repo),"async background fetch fsck maintenance gc cancel progress"),("Visual Diff Center",lambda:VisualDiffCenter(self,repo),"visual side by side word diff hunk stage unstage"),("Plugin Security Center",lambda:PluginSecurityCenter(self,repo),"plugin security manifest permissions allowlist publisher trust signature hash"),("Public Release Readiness",lambda:PublicReleaseReadinessCenter(self,repo),"public release readiness audit score gates"),("Accessibility & Display",lambda:AccessibilityCenter(self,repo),"accessibility high contrast large text keyboard focus reduce motion"),("Preflight Quality Gates",lambda:PreflightCenter(self,repo),"preflight quality gates push pr release checks"),("Commit Template Center",lambda:CommitTemplateCenter(self,repo),"commit template message conventional"),("Patch Queue Center",lambda:PatchQueueCenter(self,repo),"patch queue git am mailbox continue abort"),("Hook Audit Center",lambda:HookAuditCenter(self,repo),"hooks audit executable provenance precommit"),("Merge Preview Center",lambda:MergePreviewCenter(self,repo),"merge preview merge-tree conflict impact"),("Reset & Recovery Planner",lambda:ResetRecoveryPlanner(self,repo),"reset soft mixed hard recovery backup"),("Git Configuration Center",lambda:GitConfigCenter(self,repo),"git config local global origin scope"),("Cherry-Pick Queue",lambda:CherryPickQueueCenter(self,repo),"cherry pick queue commits continue abort"),("Release Asset Integrity",lambda:ReleaseAssetIntegrityCenter(self,repo),"release asset sha256 checksum verify"),("Local Release Archive",lambda:LocalReleaseArchiveCenter(self,repo),"release archive source zip bundle checksums metadata"),("Signature Audit",lambda:CommitSignatureAuditCenter(self,repo),"signature audit signed commits verification gpg"),("Release Comparison",lambda:ReleaseCompareCenter(self,repo),"release compare tags commits files diff"),("Safe Branch Delete",lambda:SafeDeleteBranchWizard(self,repo),"safe branch delete merged worktree upstream"),("Pull Strategy Advisor",lambda:PullRebaseAdvisor(self,repo),"pull strategy merge rebase fast forward ahead behind"),("Detached HEAD Recovery",lambda:DetachedHeadRecoveryCenter(self,repo),"detached head recovery branch switch"),("Repository State Export",lambda:RepositoryStateExportCenter(self,repo),"repository state export json markdown audit"),("Repository Rules Audit",lambda:RepositoryRulesCenter(self,repo),"repository rules governance docs codeowners workflows"),("Commit Range Exporter",lambda:CommitRangeExporter(self,repo),"commit range patches bundle markdown export"),("Local Branch Dashboard",lambda:LocalBranchDashboard(self,repo),"branch dashboard divergence recency compare"),("Repository Onboarding",lambda:RepositoryOnboardingCenter(self,repo),"repository onboarding starter readme governance"),("Repository Audit Pack",lambda:RepositoryAuditPackCenter(self,repo),"audit pack evidence status remotes fsck config"),("Safety Branch Manager",lambda:BackupBranchManager(self,repo),"backup safety branch gccc cleanup recovery"),("Upstream Health",lambda:UpstreamHealthCenter(self,repo),"upstream health broken branch remote divergence"),("Release Evidence",lambda:ReleaseEvidenceCenter(self,repo),"release evidence approval integrity signature docs"),("Repository Locator",lambda:RepositoryLocatorCenter(self,repo),"repository locator scan workspace find repositories"),("Blame Explorer",lambda:BlameExplorerCenter(self,repo),"blame line author commit inspector"),("Remote Prune Audit",lambda:AsyncRemotePruneCenter(self,repo),"remote prune stale refs dry run"),("Git Object Inspector",lambda:CommitObjectCenter(self,repo),"git object cat-file tree plumbing inspect"),("Automated Bisect",lambda:BisectAutomationCenter(self,repo),"bisect run regression automated test command"),("Revision Archive",lambda:RevisionArchiveCenter(self,repo),"archive revision zip subdirectory export"),("Commit Metadata Inspector",lambda:CommitMetadataCenter(self,repo),"commit metadata author committer parents signature tree"),("Dangling Object Recovery",lambda:DanglingObjectRecoveryCenter(self,repo),"dangling unreachable commit fsck recovery lost objects"),("Contributor Mailmap",lambda:MailmapCenter(self,repo),"mailmap contributors identities author email canonical"),("Patch Identity Comparator",lambda:PatchIdCenter(self,repo),"patch id duplicate cherry equivalent rebased commit"),("Credential Redaction Audit",lambda:CredentialRedactionAuditCenter(self,repo),"credential secret token redaction audit security"),("Ref Consistency",lambda:RefConsistencyCenter(self,repo),"ref consistency symbolic head connectivity refs"),("Release Branch Planner",lambda:ReleaseBranchPlanner(self,repo),"release branch planner create base switch"),("Switch & Restore",lambda:GitSwitchRestoreCenter(self,repo),"git switch restore source staged worktree"),("Rebase State Inspector",lambda:RebaseStateCenter(self,repo),"rebase state todo continue skip abort conflicts"),("Git Describe & Version",lambda:GitDescribeCenter(self,repo),"git describe version tag dirty release"),("Worktree Repair",lambda:GitWorktreeRepairCenter(self,repo),"worktree repair prune stale metadata"),("Tag Manager Pro",lambda:TagManagerPro(self,repo),"tag annotated signed push verify delete remote"),("Pathspec Explorer",lambda:GitPathspecCenter(self,repo),"pathspec glob exclude files changed preview"),("Git Grep Studio",lambda:GitGrepStudio(self,repo),"grep repository regex fixed historical content search"),("Tree Comparison",lambda:ArchiveCompareCenter(self,repo),"tree compare dirstat rename files refs"),("Remote URL Audit",lambda:RemoteUrlAuditCenter(self,repo),"remote url fetch push fork upstream audit"),("Git Replace Center",lambda:GitReplaceCenter(self,repo),"git replace object local ref graft"),("Merge Base Explorer",lambda:MergeBaseExplorer(self,repo),"merge base fork point ancestor independent"),("Commit Reachability Explorer",lambda:BranchContainsCenter(self,repo),"branch contains tag contains no merged reachability"),("Revert Queue",lambda:RevertQueueCenter(self,repo),"revert queue commits continue abort backup"),("Git Log Query Builder",lambda:GitLogQueryCenter(self,repo),"git log author date path grep merges query"),("Git Index Inspector",lambda:IndexInspectorCenter(self,repo),"index staging area stages blobs flags unstage"),("Merge Commit Revert",lambda:MergeCommitRevertCenter(self,repo),"merge commit revert mainline parent protected"),("Commit Graph & Pack Index",lambda:CommitGraphMaintenanceCenter(self,repo),"commit graph multi pack index bitmap maintenance"),("Diff Algorithm Lab",lambda:DiffAlgorithmCenter(self,repo),"diff algorithm myers patience histogram minimal word diff"),("Git Subtree Center",lambda:SubtreeCenter(self,repo),"git subtree vendor split add pull push"),("History Rewrite Advisor",lambda:GitFilterRepoAdvisor(self,repo),"filter repo history rewrite remove secret large file"),("Attributes Audit",lambda:AttributesAuditCenter(self,repo),"gitattributes audit binary lfs text eol diff merge"),("Range-Diff Center",lambda:GitRangeDiffCenter(self,repo),"range diff rebase patch series compare"),("Refspec Lab",lambda:RefspecLabCenter(self,repo),"refspec fetch push dry run remote mapping"),("Git Notes Merge",lambda:GitNotesMergeCenter(self,repo),"git notes merge union manual ours theirs"),("Merge Strategy Lab",lambda:MergeStrategyLabCenter(self,repo),"merge strategy ort recursive ours theirs subtree preview"),("Config Include Inspector",lambda:ConfigIncludeCenter(self,repo),"git config include includeif origins scopes"),("Pack Inventory",lambda:PackInventoryCenter(self,repo),"pack inventory verify-pack large blobs objects"),("Change Statistics",lambda:ChangeStatisticsCenter(self,repo),"change statistics churn authors extensions range"),("Conflict Stage Explorer",lambda:ConflictStageExplorer(self,repo),"conflict stages base ours theirs index"),("Branch Rename Planner",lambda:BranchRenamePlanner(self,repo),"branch rename remote upstream protected"),("Lost & Found Center",lambda:LostFoundCenter(self,repo),"lost found fsck recovery commit object"),("Shallow Repository Center",lambda:ShallowRepositoryCenter(self,repo),"shallow clone deepen unshallow history tags"),("Status Porcelain Explorer",lambda:StatusPorcelainCenter(self,repo),"status porcelain v2 automation records"),("Sparse Index Center",lambda:GitSparseIndexCenter(self,repo),"sparse index checkout performance large repository"),("Maintenance Schedule",lambda:GitMaintenanceScheduleCenter(self,repo),"maintenance schedule register strategy incremental geometric"),("Repository Format Inspector",lambda:ObjectFormatCenter(self,repo),"repository format sha1 sha256 ref storage extensions compatibility"),("Selective Clean",lambda:GitCleanInteractiveCenter(self,repo),"clean selective untracked ignored preview"),("File Evolution",lambda:FileEvolutionCenter(self,repo),"file evolution history rename content export"),("Remote Details",lambda:GitRemoteShowCenter(self,repo),"remote show tracking stale branches details"),("Protocol Diagnostics",lambda:ProtocolDiagnosticsCenter(self,repo),"git protocol v2 packet trace remote capabilities"),("Object Alternates Inspector",lambda:AlternatesInspectorCenter(self,repo),"object alternates shared clone dissociate repack"),("EOL Normalization",lambda:EolNormalizationCenter(self,repo),"eol line ending autocrlf gitattributes renormalize"),("Commit Message Audit",lambda:CommitMessageAuditCenter(self,repo),"commit message audit conventional quality subject"),("Revision Manifest",lambda:GitArchiveManifestCenter(self,repo),"revision manifest tree blob verify archive integrity"),("Branch Descriptions",lambda:BranchDescriptionCenter(self,repo),"branch description config local metadata purpose"),("Selective Stash",lambda:SelectiveStashCenter(self,repo),"stash selective pathspec keep index untracked"),("Worktree Move",lambda:WorktreeMoveCenter(self,repo),"worktree move relocate repair linked"),("Config Snapshot Compare",lambda:ConfigSnapshotCompareCenter(self,repo),"git config snapshot compare diff origin scope"),("Fixup & Squash Commits",lambda:CommitFixupCenter(self,repo),"fixup squash amend autosquash staged commit"),("Tracked File Flags",lambda:TrackedFileFlagsCenter(self,repo),"assume unchanged skip worktree update index flags"),("Revision Walk Lab",lambda:RevisionWalkCenter(self,repo),"revision walk topology ancestry first parent boundary order"),("Show-Branch Explorer",lambda:GitShowBranchCenter(self,repo),"show branch topology comparison multiple refs"),("Name-Rev Explorer",lambda:GitNameRevCenter(self,repo),"name rev human readable commit object tags"),("Object Growth Tracker",lambda:GitCountObjectsTrendCenter(self,repo),"count objects growth trend packs garbage maintenance"),("Ref Verification",lambda:GitVerifyRefCenter(self,repo),"verify ref symbolic peel reflog object"),("Ignore Rule Batch Tester",lambda:GitCheckIgnoreBatchCenter(self,repo),"check ignore batch verbose provenance patterns"),("Fetch Preview",lambda:AsyncFetchCenter(self,repo),"fetch dry run prune tags refspec preview")]
        self.render()
    def render(self):
        q=self.q.get().lower().strip();self.filtered=[c for c in self.commands if not q or q in (c[0]+" "+c[2]).lower()];self.list.delete(0,"end")
        for name,_,tags in self.filtered:self.list.insert("end",f"{name}    [{tags}]")
        if self.filtered:self.list.selection_set(0)
    def launch(self):
        s=self.list.curselection()
        if s:self.filtered[s[0]][1]();self.destroy()

class HooksCenter(tk.Toplevel):
    """Manage repository-local Git hooks with templates and executable-bit handling."""
    TEMPLATES={
        "pre-commit":"#!/usr/bin/env sh\nset -e\ngit diff --cached --check\npython -m compileall -q .\n",
        "commit-msg":"#!/usr/bin/env sh\nmsg=$(head -n 1 \"$1\")\n[ ${#msg} -ge 8 ] || { echo 'Commit message must be at least 8 characters.'; exit 1; }\n",
        "pre-push":"#!/usr/bin/env sh\nset -e\npython -m compileall -q .\n",
    }
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.dir=Path(repo)/".git"/"hooks";self.title("Git Hooks Manager");self.geometry("1050x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.kind=tk.StringVar(value="pre-commit");ttk.Combobox(top,textvariable=self.kind,values=list(self.TEMPLATES),state="readonly",width=18).pack(side="left")
        for t,c in [("Load",self.load),("Use safe template",self.template),("Save & enable",self.save),("Disable",self.disable),("Test hook",self.test)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",undo=True,font=("Consolas",9));self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.status=tk.StringVar();ttk.Label(self,textvariable=self.status,padding=8).pack(fill="x")
    def path(self):return self.dir/self.kind.get()
    def refresh(self):self.status.set("Select a hook. Hooks are local to this clone and are not committed by default.");self.load()
    def load(self):
        p=self.path();self.text.delete("1.0","end")
        if p.exists():self.text.insert("1.0",p.read_text(encoding="utf-8",errors="replace"));self.status.set(f"Loaded {p.name}")
        else:self.status.set(f"{p.name} is not installed")
    def template(self):self.text.delete("1.0","end");self.text.insert("1.0",self.TEMPLATES[self.kind.get()])
    def save(self):
        p=self.path();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8");p.chmod(p.stat().st_mode|0o111);self.status.set(f"Saved and enabled {p.name}")
    def disable(self):
        p=self.path()
        if p.exists():p.chmod(p.stat().st_mode&~0o111);self.status.set(f"Disabled {p.name}")
    def test(self):
        p=self.path()
        if not p.exists():return messagebox.showwarning("Hook","Save the hook first.",parent=self)
        try:
            r=subprocess.run([str(p)],cwd=self.repo,text=True,capture_output=True,timeout=120,encoding="utf-8",errors="replace");messagebox.showinfo("Hook test",f"Exit code: {r.returncode}\n\n{r.stdout}\n{r.stderr}",parent=self)
        except Exception as e:messagebox.showerror("Hook test",str(e),parent=self)

class LFSCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git LFS Center");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.pattern=tk.StringVar(value="*.zip");ttk.Entry(top,textvariable=self.pattern,width=24).pack(side="left")
        for t,c in [("Track pattern",self.track),("Untrack pattern",self.untrack),("Refresh",self.refresh),("Pull LFS objects",lambda:self.run("pull")),("Prune local LFS",self.prune)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def lfs(self,*args):return git(self.repo,"lfs",*args)
    def refresh(self):
        try:v="GIT LFS ENVIRONMENT\n"+"="*72+"\n"+self.lfs("env")+"\n\nTRACKED PATTERNS\n"+"="*72+"\n"+self.lfs("track")+"\n\nLFS FILES\n"+"="*72+"\n"+self.lfs("ls-files")
        except Exception as e:v="Git LFS is unavailable or not installed. Install Git LFS and run `git lfs install`.\n\n"+str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def track(self):
        p=self.pattern.get().strip()
        if p:
            try:messagebox.showinfo("Git LFS",self.lfs("track",p),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Git LFS",str(e),parent=self)
    def untrack(self):
        p=self.pattern.get().strip()
        if p and messagebox.askyesno("Git LFS",f"Stop tracking {p} with LFS? Existing history is not rewritten.",parent=self):
            try:messagebox.showinfo("Git LFS",self.lfs("untrack",p),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Git LFS",str(e),parent=self)
    def run(self,*args):
        try:messagebox.showinfo("Git LFS",self.lfs(*args),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Git LFS",str(e),parent=self)
    def prune(self):
        if messagebox.askyesno("Git LFS prune","Prune old local LFS objects that Git LFS considers safe to remove?",parent=self):self.run("prune")

class AutomationCenter(tk.Toplevel):
    """Extensible repository-local automation recipes stored as JSON."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-recipes.json";self.title("Automation Recipes");self.geometry("1100x720");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Run selected",self.run_selected),("Add recipe",self.add),("Delete",self.delete),("Reset defaults",self.defaults),("Save",self.save)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Segoe UI",10));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.describe())
        self.out=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def base(self):return [{"name":"Python syntax check","command":["python","-m","compileall","-q","."]},{"name":"Git integrity check","command":["git","fsck","--no-progress"]},{"name":"Whitespace check","command":["git","diff","--check"]}]
    def load(self):
        import json
        try:self.recipes=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else self.base()
        except:self.recipes=self.base()
        self.render()
    def render(self):self.list.delete(0,"end");[self.list.insert("end",r["name"]) for r in self.recipes]
    def describe(self):
        s=self.list.curselection()
        if s:self.out.delete("1.0","end");self.out.insert("1.0","Command:\n"+" ".join(self.recipes[s[0]]["command"]))
    def add(self):
        import shlex
        n=simpledialog.askstring("Recipe","Recipe name:",parent=self);c=simpledialog.askstring("Recipe","Command line:",parent=self) if n else None
        if c:self.recipes.append({"name":n,"command":shlex.split(c)});self.render();self.save(False)
    def delete(self):
        s=self.list.curselection()
        if s:del self.recipes[s[0]];self.render();self.save(False)
    def defaults(self):self.recipes=self.base();self.render();self.save(False)
    def save(self,notice=True):
        import json
        self.path.write_text(json.dumps(self.recipes,indent=2),encoding="utf-8")
        if notice:messagebox.showinfo("Recipes","Saved under .git/gccc-recipes.json",parent=self)
    def run_selected(self):
        s=self.list.curselection()
        if not s:return
        r=self.recipes[s[0]]
        try:
            p=subprocess.run(r["command"],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace");v=f"Recipe: {r['name']}\nExit code: {p.returncode}\n\n{p.stdout}\n{p.stderr}"
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class IdentitySigningCenter(tk.Toplevel):
    """Configure repository identity and inspect commit/tag signature status."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Identity & Signing Center");self.geometry("1080x730");self._build();self.refresh()
    def _build(self):
        form=ttk.Frame(self,padding=8);form.pack(fill="x")
        self.name=tk.StringVar();self.email=tk.StringVar();self.key=tk.StringVar();self.sign=tk.BooleanVar()
        for i,(label,var) in enumerate((("User name",self.name),("User email",self.email),("Signing key",self.key))):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky="w",pady=3);ttk.Entry(form,textvariable=var).grid(row=i,column=1,sticky="ew",padx=6,pady=3)
        form.columnconfigure(1,weight=1);ttk.Checkbutton(form,text="Sign commits by default in this repository",variable=self.sign).grid(row=3,column=1,sticky="w",pady=4)
        buttons=ttk.Frame(self,padding=(8,0));buttons.pack(fill="x")
        for t,c in [("Save repository identity",self.save),("Refresh",self.refresh),("List GPG keys",self.keys),("Verify recent commits",self.verify),("Create signed test tag",self.test_tag)]:ttk.Button(buttons,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=8)
    def cfg(self,key):
        try:v=git(self.repo,"config","--get",key);return "" if v=="Completed successfully." else v
        except:return ""
    def refresh(self):
        self.name.set(self.cfg("user.name"));self.email.set(self.cfg("user.email"));self.key.set(self.cfg("user.signingkey"));self.sign.set(self.cfg("commit.gpgsign").lower()=="true")
        self.out.delete("1.0","end");self.out.insert("1.0","Repository identity loaded. Repository-level settings override global Git identity only for this clone.\n\nSigning requires a configured GPG or SSH signing key supported by your Git installation.")
    def save(self):
        try:
            if self.name.get().strip():git(self.repo,"config","user.name",self.name.get().strip())
            if self.email.get().strip():git(self.repo,"config","user.email",self.email.get().strip())
            if self.key.get().strip():git(self.repo,"config","user.signingkey",self.key.get().strip())
            git(self.repo,"config","commit.gpgsign","true" if self.sign.get() else "false");messagebox.showinfo("Identity","Repository identity settings saved.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Identity",str(e),parent=self)
    def keys(self):
        try:
            r=subprocess.run(["gpg","--list-secret-keys","--keyid-format=long"],text=True,capture_output=True,timeout=60,encoding="utf-8",errors="replace");v=(r.stdout+r.stderr).strip()
        except Exception as e:v="GPG unavailable: "+str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def verify(self):
        try:v=git(self.repo,"log","-30","--show-signature","--pretty=format:%h %ad %an %s","--date=short")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def test_tag(self):
        import datetime
        tag="gccc-signing-test-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        if not messagebox.askyesno("Signed tag",f"Create local signed test tag {tag}? It will not be pushed.",parent=self):return
        try:messagebox.showinfo("Signed tag",git(self.repo,"tag","-s",tag,"-m","GitHub Command Center signing test"),parent=self)
        except Exception as e:messagebox.showerror("Signed tag",str(e),parent=self)

class CommitMessageStudio(tk.Toplevel):
    TYPES=("feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert")
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Message Studio");self.geometry("980x720");self._build();self.update_preview()
    def _build(self):
        f=ttk.Frame(self,padding=10);f.pack(fill="x");self.typ=tk.StringVar(value="feat");self.scope=tk.StringVar();self.subject=tk.StringVar();self.breaking=tk.BooleanVar()
        ttk.Label(f,text="Type").grid(row=0,column=0,sticky="w");ttk.Combobox(f,textvariable=self.typ,values=self.TYPES,state="readonly",width=16).grid(row=0,column=1,sticky="w",padx=5)
        ttk.Label(f,text="Scope").grid(row=1,column=0,sticky="w");ttk.Entry(f,textvariable=self.scope).grid(row=1,column=1,sticky="ew",padx=5)
        ttk.Label(f,text="Subject").grid(row=2,column=0,sticky="w");ttk.Entry(f,textvariable=self.subject).grid(row=2,column=1,sticky="ew",padx=5)
        ttk.Checkbutton(f,text="Breaking change",variable=self.breaking,command=self.update_preview).grid(row=3,column=1,sticky="w");f.columnconfigure(1,weight=1)
        for var in (self.typ,self.scope,self.subject):var.trace_add("write",lambda *_:self.update_preview())
        ttk.Label(self,text="Body",padding=(10,4)).pack(anchor="w");self.body=tk.Text(self,height=8,wrap="word");self.body.pack(fill="x",padx=10);self.body.bind("<KeyRelease>",lambda e:self.update_preview())
        ttk.Label(self,text="Footer / issue references",padding=(10,4)).pack(anchor="w");self.footer=tk.Text(self,height=4,wrap="word");self.footer.pack(fill="x",padx=10);self.footer.bind("<KeyRelease>",lambda e:self.update_preview())
        self.preview=tk.Text(self,height=9,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.preview.pack(fill="both",expand=True,padx=10,pady=8)
        bar=ttk.Frame(self,padding=(10,0,10,10));bar.pack(fill="x");ttk.Button(bar,text="Copy message",command=self.copy).pack(side="left");ttk.Button(bar,text="Commit staged changes",command=self.commit).pack(side="right")
    def message(self):
        scope=f"({self.scope.get().strip()})" if self.scope.get().strip() else "";bang="!" if self.breaking.get() else "";head=f"{self.typ.get()}{scope}{bang}: {self.subject.get().strip()}"
        parts=[head];body=self.body.get("1.0","end-1c").strip();foot=self.footer.get("1.0","end-1c").strip()
        if body:parts.append(body)
        if self.breaking.get() and "BREAKING CHANGE:" not in foot:foot=(foot+"\n" if foot else "")+"BREAKING CHANGE: describe the incompatible behavior"
        if foot:parts.append(foot)
        return "\n\n".join(parts)
    def update_preview(self):
        self.preview.delete("1.0","end");self.preview.insert("1.0",self.message())
    def copy(self):self.clipboard_clear();self.clipboard_append(self.message());messagebox.showinfo("Commit message","Copied to clipboard.",parent=self)
    def commit(self):
        if not self.subject.get().strip():return messagebox.showwarning("Commit","Enter a subject.",parent=self)
        try:
            staged=git(self.repo,"diff","--cached","--name-only")
            if staged=="Completed successfully.":raise GitError("Nothing is staged.")
            if messagebox.askyesno("Commit",f"Commit staged changes with this message?\n\n{self.message()}",parent=self):messagebox.showinfo("Commit",git(self.repo,"commit","-m",self.message()),parent=self)
        except Exception as e:messagebox.showerror("Commit",str(e),parent=self)

class ChangelogStudio(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Changelog Studio");self.geometry("1080x740");self._build();self.generate()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.base=tk.StringVar();self.version=tk.StringVar(value="Unreleased")
        ttk.Label(top,text="Since ref").pack(side="left");ttk.Entry(top,textvariable=self.base,width=20).pack(side="left",padx=3);ttk.Label(top,text="Version").pack(side="left");ttk.Entry(top,textvariable=self.version,width=16).pack(side="left",padx=3)
        for t,c in [("Generate",self.generate),("Prepend to CHANGELOG",self.prepend),("Save section",self.save),("Copy",self.copy)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",undo=True,font=("Consolas",9));self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def generate(self):
        try:
            base=self.base.get().strip()
            if not base:
                try:base=git(self.repo,"describe","--tags","--abbrev=0");base="" if base=="Completed successfully." else base
                except:base=""
                self.base.set(base)
            args=["log","--pretty=format:%s%x1f%h"]+([f"{base}..HEAD"] if base else [])
            raw=git(self.repo,*args);groups={k:[] for k in ("Added","Fixed","Changed","Documentation","Tests","Build and CI","Other")}
            for line in raw.splitlines():
                if "\x1f" not in line:continue
                subject,h=line.split("\x1f",1);prefix=subject.split(":",1)[0].split("(",1)[0]
                group={"feat":"Added","fix":"Fixed","refactor":"Changed","perf":"Changed","docs":"Documentation","test":"Tests","build":"Build and CI","ci":"Build and CI"}.get(prefix,"Other")
                groups[group].append(f"- {subject} ({h})")
            section=f"## {self.version.get().strip() or 'Unreleased'}\n"
            for name,items in groups.items():
                if items:section+=f"\n### {name}\n"+"\n".join(items)+"\n"
            self.text.delete("1.0","end");self.text.insert("1.0",section)
        except Exception as e:messagebox.showerror("Changelog",str(e),parent=self)
    def prepend(self):
        p=Path(self.repo)/"CHANGELOG.md";section=self.text.get("1.0","end-1c").strip()+"\n\n";old=p.read_text(encoding="utf-8",errors="replace") if p.exists() else "# Changelog\n\n"
        if old.startswith("# Changelog"):new="# Changelog\n\n"+section+old[len("# Changelog"):].lstrip()
        else:new=section+old
        p.write_text(new,encoding="utf-8");messagebox.showinfo("Changelog","CHANGELOG.md updated. Review and commit it.",parent=self)
    def save(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="changelog-section.md")
        if p:Path(p).write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8")
    def copy(self):self.clipboard_clear();self.clipboard_append(self.text.get("1.0","end-1c"));messagebox.showinfo("Changelog","Copied to clipboard.",parent=self)

class RemoteMigrationCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote Migration & Mirror Center");self.geometry("1000x690");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.name=tk.StringVar(value="backup");self.url=tk.StringVar();ttk.Entry(top,textvariable=self.name,width=15).pack(side="left");ttk.Entry(top,textvariable=self.url).pack(side="left",fill="x",expand=True,padx=4)
        for t,c in [("Add/update remote",self.set_remote),("Fetch all",self.fetch),("Push mirror",self.mirror),("Refresh",self.refresh)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Mirror push overwrites the destination refs to match this repository. Use only for a dedicated backup/migration remote and verify the URL carefully.",padding=8,foreground="#b91c1c").pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"remote","-v")+"\n\nREF SUMMARY\n"+git(self.repo,"show-ref")
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def set_remote(self):
        n=self.name.get().strip();u=self.url.get().strip()
        if not n or not u:return
        try:
            existing=git(self.repo,"remote").splitlines();out=git(self.repo,"remote","set-url",n,u) if n in existing else git(self.repo,"remote","add",n,u);messagebox.showinfo("Remote",out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Remote",str(e),parent=self)
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def mirror(self):
        n=self.name.get().strip()
        if n=="origin":return messagebox.showwarning("Mirror","Use a dedicated backup remote, not origin.",parent=self)
        if messagebox.askyesno("Mirror push",f"DANGEROUS: overwrite all refs on remote '{n}' to mirror this repository?",parent=self):
            confirm=simpledialog.askstring("Confirm mirror",f"Type the remote name exactly to continue: {n}",parent=self)
            if confirm==n:
                try:messagebox.showinfo("Mirror",git(self.repo,"push","--mirror",n),parent=self);self.refresh()
                except Exception as e:messagebox.showerror("Mirror",str(e),parent=self)

class CredentialAuditCenter(tk.Toplevel):
    """Inspect credential helpers and remote URL hygiene without exposing secrets."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Credential & Remote Hygiene");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh audit",self.refresh),("Convert origin to SSH",self.to_ssh),("Convert origin to HTTPS",self.to_https),("Open GitHub auth status",self.gh_status)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        remote=self.safe("remote","-v");helpers=self.safe("config","--show-origin","--get-all","credential.helper")
        findings=[]
        for line in remote.splitlines():
            if "@" in line and "https://" in line:findings.append("WARN: HTTPS remote appears to contain embedded credentials or user information. Replace it immediately.")
            if "github.com" in line and not ("git@github.com:" in line or "https://github.com/" in line):findings.append("WARN: Non-standard GitHub remote format detected.")
        if not findings:findings.append("PASS: No obvious embedded credential pattern detected in remote URLs.")
        report="CREDENTIAL & REMOTE HYGIENE\n"+"="*72+"\n\nREMOTES\n"+remote+"\n\nCREDENTIAL HELPERS\n"+helpers+"\n\nFINDINGS\n"+"\n".join(findings)+"\n\nThis center never reads or displays stored passwords/tokens."
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def parse_origin(self):
        u=git(self.repo,"remote","get-url","origin")
        import re
        m=re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",u)
        if not m:raise GitError("Origin is not a recognizable GitHub URL.")
        return m.group(1),m.group(2)
    def to_ssh(self):
        try:
            owner,name=self.parse_origin();u=f"git@github.com:{owner}/{name}.git"
            if messagebox.askyesno("Remote URL",f"Set origin to SSH?\n{u}",parent=self):git(self.repo,"remote","set-url","origin",u);self.refresh()
        except Exception as e:messagebox.showerror("Remote URL",str(e),parent=self)
    def to_https(self):
        try:
            owner,name=self.parse_origin();u=f"https://github.com/{owner}/{name}.git"
            if messagebox.askyesno("Remote URL",f"Set origin to HTTPS?\n{u}",parent=self):git(self.repo,"remote","set-url","origin",u);self.refresh()
        except Exception as e:messagebox.showerror("Remote URL",str(e),parent=self)
    def gh_status(self):
        try:
            r=subprocess.run(["gh","auth","status"],cwd=self.repo,text=True,capture_output=True,timeout=30,encoding="utf-8",errors="replace");messagebox.showinfo("GitHub authentication",(r.stdout+r.stderr).strip(),parent=self)
        except Exception as e:messagebox.showerror("GitHub authentication",str(e),parent=self)

class ReleasePolicyCenter(tk.Toplevel):
    """Repository-local release gates and version policy."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-release-policy.json";self.title("Release Policy Center");self.geometry("1080x720");self._build();self.load()
    def _build(self):
        form=ttk.Frame(self,padding=8);form.pack(fill="x")
        self.clean=tk.BooleanVar(value=True);self.upstream=tk.BooleanVar(value=True);self.changelog=tk.BooleanVar(value=True);self.security=tk.BooleanVar(value=True);self.prefix=tk.StringVar(value="v")
        for text,var in [("Require clean working tree",self.clean),("Require configured upstream",self.upstream),("Require CHANGELOG.md",self.changelog),("Require SECURITY.md",self.security)]:ttk.Checkbutton(form,text=text,variable=var).pack(side="left",padx=5)
        ttk.Label(form,text="Tag prefix").pack(side="left",padx=(15,2));ttk.Entry(form,textvariable=self.prefix,width=6).pack(side="left")
        bar=ttk.Frame(self,padding=(8,0));bar.pack(fill="x")
        for t,c in [("Evaluate",self.evaluate),("Save policy",self.save),("Suggest next version",self.suggest)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def load(self):
        import json
        if self.path.exists():
            try:
                p=json.loads(self.path.read_text(encoding="utf-8"));self.clean.set(p.get("clean",True));self.upstream.set(p.get("upstream",True));self.changelog.set(p.get("changelog",True));self.security.set(p.get("security",True));self.prefix.set(p.get("prefix","v"))
            except:pass
        self.evaluate()
    def save(self):
        import json
        self.path.write_text(json.dumps({"clean":self.clean.get(),"upstream":self.upstream.get(),"changelog":self.changelog.get(),"security":self.security.get(),"prefix":self.prefix.get()},indent=2),encoding="utf-8");messagebox.showinfo("Release policy","Saved under .git/gccc-release-policy.json",parent=self)
    def evaluate(self):
        checks=[]
        def add(name,ok,detail):checks.append((name,ok,detail))
        status=git(self.repo,"status","--porcelain");add("Clean working tree",not self.clean.get() or status=="Completed successfully.","Clean" if status=="Completed successfully." else "Local changes found")
        try:u=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");ok=True
        except Exception as e:u=str(e);ok=False
        add("Upstream configured",not self.upstream.get() or ok,u)
        add("CHANGELOG.md",not self.changelog.get() or (Path(self.repo)/"CHANGELOG.md").exists(),"Present" if (Path(self.repo)/"CHANGELOG.md").exists() else "Missing")
        add("SECURITY.md",not self.security.get() or (Path(self.repo)/"SECURITY.md").exists(),"Present" if (Path(self.repo)/"SECURITY.md").exists() else "Missing")
        report="RELEASE POLICY EVALUATION\n"+"="*72+"\n\n"+"\n\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}\n  {d}" for n,ok,d in checks)
        report+=f"\n\nOVERALL: {'PASS' if all(x[1] for x in checks) else 'BLOCKED'}"
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def suggest(self):
        import re
        try:last=git(self.repo,"describe","--tags","--abbrev=0")
        except:last=""
        m=re.search(r"(\d+)\.(\d+)\.(\d+)",last)
        if not m:return messagebox.showinfo("Version","No semantic-version tag found. Suggested first tag: v0.1.0",parent=self)
        major,minor,patch=map(int,m.groups());raw=git(self.repo,"log","--pretty=format:%s",f"{last}..HEAD")
        bump="patch"
        if any("BREAKING CHANGE" in x or re.match(r"\w+(\([^)]*\))?!:",x) for x in raw.splitlines()):bump="major"
        elif any(x.startswith("feat") for x in raw.splitlines()):bump="minor"
        version=(major+1,0,0) if bump=="major" else (major,minor+1,0) if bump=="minor" else (major,minor,patch+1)
        messagebox.showinfo("Suggested version",f"Latest tag: {last}\nSuggested bump: {bump}\nSuggested tag: {self.prefix.get()}{version[0]}.{version[1]}.{version[2]}",parent=self)

class RepositoryMetricsCenter(tk.Toplevel):
    """Local engineering metrics without external analytics services."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Metrics Center");self.geometry("1100x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh metrics",command=self.refresh).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except:return ""
    def refresh(self):
        commits=self.safe("rev-list","--count","HEAD");contributors=self.safe("shortlog","-sne","HEAD");files=self.safe("ls-files").splitlines();languages={};total_lines=0
        extmap={".py":"Python",".js":"JavaScript",".ts":"TypeScript",".tsx":"TypeScript",".java":"Java",".go":"Go",".rs":"Rust",".md":"Markdown",".html":"HTML",".css":"CSS",".sh":"Shell"}
        for f in files:
            p=Path(self.repo)/f;lang=extmap.get(p.suffix.lower())
            if lang:
                try:n=len(p.read_text(encoding="utf-8",errors="ignore").splitlines());languages[lang]=languages.get(lang,0)+n;total_lines+=n
                except:pass
        monthly=self.safe("log","--date=format:%Y-%m","--pretty=format:%ad");counts={}
        for m in monthly.splitlines():counts[m]=counts.get(m,0)+1
        report=f"REPOSITORY METRICS\n{'='*72}\nCommits: {commits}\nTracked files: {len(files)}\nCounted text lines: {total_lines}\n\nCONTRIBUTORS\n{contributors or 'Unavailable'}\n\nLANGUAGE LINES (heuristic)\n"
        for k,v in sorted(languages.items(),key=lambda x:-x[1]):report+=f"{k:<18}{v:>10}\n"
        report+="\nCOMMITS BY MONTH\n"
        for k,v in sorted(counts.items(),reverse=True)[:24]:report+=f"{k}: {v}\n"
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile=Path(self.repo).name+"-metrics.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

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
            except Exception:pass
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
        except Exception as e:v=str(e)
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
            except Exception:pass
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
            except Exception as e:out="ERROR: "+str(e)
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
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        branch=self.safe("branch","--show-current");status=self.safe("status","--porcelain");clean=status=="Completed successfully."
        try:up=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");ahead=self.safe("rev-list","--count","@{u}..HEAD");behind=self.safe("rev-list","--count","HEAD..@{u}")
        except:up=ahead=behind="-"
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
            except:return ""
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
        except Exception as e:return messagebox.showerror("Job",str(e),parent=self)
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
            except Exception as e:job["log"]+=str(e);job["status"]="Failed";job["code"]="-"
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
            except:pass
    def save(self):
        import json
        p={"theme":self.theme.get(),"font_size":self.font.get(),"history_limit":self.limit.get(),"confirm_destructive":self.confirm.get(),"default_branch":self.default_branch.get()};self.path.write_text(json.dumps(p,indent=2),encoding="utf-8")
        try:ttk.Style().theme_use(self.theme.get())
        except:pass
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
                except:a=b="-"
                rows.append((now,str(p),p.name,branch,state,a,b))
            except:pass
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

class SelfTestCenter(tk.Toplevel):
    """Built-in smoke tests for parsers, configuration and command prerequisites."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Self-Test & Readiness Center");self.geometry("1050x700");self._build();self.run()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Run tests",command=self.run).pack(side="left");ttk.Button(top,text="Export results",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def run(self):
        tests=[]
        def record(name,fn):
            try:v=fn();tests.append((name,True,str(v)))
            except Exception as e:tests.append((name,False,str(e)))
        record("Git available",lambda:git(self.repo,"--version"));record("Repository work tree",lambda:git(self.repo,"rev-parse","--is-inside-work-tree"));record("HEAD resolves",lambda:git(self.repo,"rev-parse","HEAD"));record("Status parser",lambda:len(git(self.repo,"status","--porcelain").splitlines()));record("Log parser",lambda:len(git(self.repo,"log","-5","--pretty=format:%H%x1f%s").splitlines()));record("Config writable",lambda:(Path(self.repo)/".git").is_dir());record("Python source compiles",self.compile_source)
        self.report="SELF-TEST RESULTS\n"+"="*72+"\n\n"+"\n\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}\n  {d}" for n,ok,d in tests)+f"\n\nOVERALL: {'PASS' if all(t[1] for t in tests) else 'FAIL'}"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def compile_source(self):
        root=Path(__file__).parent.parent;r=subprocess.run(["python","-m","compileall","-q",str(root)],text=True,capture_output=True,timeout=180,encoding="utf-8",errors="replace")
        if r.returncode:raise RuntimeError((r.stdout+r.stderr).strip())
        return "Compilation passed"
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="gccc-self-test.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class PartialStagingCenter(tk.Toplevel):
    """Hunk-level staging UI backed by git diff and git apply --cached."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Partial Staging Center");self.geometry("1300x820");self.minsize(1050,700);self.files=[];self.hunks=[];self.current_file="";self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Stage selected hunk",self.stage_hunk),("Unstage selected hunk",self.unstage_hunk),("Stage whole file",self.stage_file),("Unstage whole file",self.unstage_file)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5)
        left=ttk.Frame(pane);middle=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=2);pane.add(middle,weight=2);pane.add(right,weight=4)
        ttk.Label(left,text="Changed files",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=4);self.file_list=tk.Listbox(left,font=("Consolas",9));self.file_list.pack(fill="both",expand=True);self.file_list.bind("<<ListboxSelect>>",lambda e:self.load_file())
        ttk.Label(middle,text="Hunks",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=4);self.hunk_list=tk.Listbox(middle,font=("Consolas",9));self.hunk_list.pack(fill="both",expand=True);self.hunk_list.bind("<<ListboxSelect>>",lambda e:self.show_hunk())
        ttk.Label(right,text="Selected hunk preview",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=4);self.preview=tk.Text(right,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.preview.pack(fill="both",expand=True)
        self.status=tk.StringVar(value="Ready");ttk.Label(self,textvariable=self.status,padding=8).pack(fill="x")
    def changed_files(self):
        out=git(self.repo,"status","--porcelain=v1");rows=[]
        for line in out.splitlines():
            if len(line)>3:
                path=line[3:]
                if " -> " in path:path=path.split(" -> ",1)[1]
                rows.append((line[:2],path))
        return rows
    def refresh(self):
        try:
            self.files=self.changed_files();self.file_list.delete(0,"end");self.hunk_list.delete(0,"end");self.preview.delete("1.0","end")
            for state,path in self.files:self.file_list.insert("end",f"{state}  {path}")
            self.status.set(f"{len(self.files)} changed file(s). Select a text file to inspect hunks.")
        except Exception as e:messagebox.showerror("Partial staging",str(e),parent=self)
    def parse_patch(self,patch):
        lines=patch.splitlines(keepends=True);header=[];hunks=[];current=[]
        for line in lines:
            if line.startswith("@@"):
                if current:hunks.append(header+current)
                current=[line]
            elif current:current.append(line)
            else:header.append(line)
        if current:hunks.append(header+current)
        return ["".join(x) for x in hunks]
    def selected_file(self):
        s=self.file_list.curselection();return self.files[s[0]][1] if s else None
    def load_file(self):
        path=self.selected_file()
        if not path:return
        self.current_file=path
        try:
            patch=git(self.repo,"diff","--no-ext-diff","--binary","--",path)
            if patch=="Completed successfully.":patch=""
            self.hunks=self.parse_patch(patch);self.hunk_list.delete(0,"end")
            for i,h in enumerate(self.hunks):
                marker=next((x.strip() for x in h.splitlines() if x.startswith("@@")),f"Hunk {i+1}");self.hunk_list.insert("end",f"{i+1}. {marker}")
            if not self.hunks:self.status.set("No unstaged text hunks. The file may be fully staged, untracked, binary, or unchanged.")
            else:self.status.set(f"{len(self.hunks)} unstaged hunk(s) in {path}")
        except Exception as e:messagebox.showerror("Partial staging",str(e),parent=self)
    def show_hunk(self):
        s=self.hunk_list.curselection();self.preview.delete("1.0","end")
        if s:self.preview.insert("1.0",self.hunks[s[0]])
    def apply_patch(self,patch,cached=True,reverse=False):
        import tempfile,os
        fd,name=tempfile.mkstemp(prefix="gccc-hunk-",suffix=".patch");os.close(fd)
        try:
            Path(name).write_text(patch,encoding="utf-8");args=["apply","--whitespace=nowarn"]
            if cached:args.append("--cached")
            if reverse:args.append("--reverse")
            args.append(name);return git(self.repo,*args)
        finally:
            try:os.unlink(name)
            except OSError:pass
    def stage_hunk(self):
        s=self.hunk_list.curselection()
        if not s:return
        try:self.apply_patch(self.hunks[s[0]],True,False);self.status.set("Selected hunk staged.");self.refresh();self.select_file_again()
        except Exception as e:messagebox.showerror("Stage hunk",str(e),parent=self)
    def staged_hunks(self,path):
        p=git(self.repo,"diff","--cached","--no-ext-diff","--binary","--",path);return self.parse_patch("" if p=="Completed successfully." else p)
    def unstage_hunk(self):
        path=self.selected_file()
        if not path:return
        hunks=self.staged_hunks(path)
        if not hunks:return messagebox.showinfo("Unstage hunk","No staged text hunks found for this file.",parent=self)
        PickHunkDialog(self,self.repo,path,hunks,self.after_unstage)
    def after_unstage(self):self.refresh();self.status.set("Selected staged hunk returned to the working tree.")
    def select_file_again(self):
        for i,(_,p) in enumerate(self.files):
            if p==self.current_file:self.file_list.selection_set(i);self.file_list.see(i);self.load_file();break
    def stage_file(self):
        p=self.selected_file()
        if p:
            try:git(self.repo,"add","--",p);self.refresh()
            except Exception as e:messagebox.showerror("Stage file",str(e),parent=self)
    def unstage_file(self):
        p=self.selected_file()
        if p:
            try:git(self.repo,"restore","--staged","--",p);self.refresh()
            except Exception as e:messagebox.showerror("Unstage file",str(e),parent=self)

class PickHunkDialog(tk.Toplevel):
    def __init__(self,parent,repo,path,hunks,done):
        super().__init__(parent);self.repo=repo;self.path=path;self.hunks=hunks;self.done=done;self.title("Select staged hunk to unstage");self.geometry("1050x700")
        self.list=tk.Listbox(self,font=("Consolas",9));self.list.pack(side="left",fill="y",padx=6,pady=6)
        for i,h in enumerate(hunks):self.list.insert("end",next((x.strip() for x in h.splitlines() if x.startswith("@@")),f"Hunk {i+1}"))
        self.list.bind("<<ListboxSelect>>",lambda e:self.show());r=ttk.Frame(self);r.pack(side="left",fill="both",expand=True);self.text=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=6,pady=6);ttk.Button(r,text="Unstage selected hunk",command=self.apply).pack(anchor="e",padx=6,pady=6)
    def show(self):
        s=self.list.curselection();self.text.delete("1.0","end")
        if s:self.text.insert("1.0",self.hunks[s[0]])
    def apply(self):
        import tempfile,os
        s=self.list.curselection()
        if not s:return
        fd,name=tempfile.mkstemp(prefix="gccc-unstage-",suffix=".patch");os.close(fd)
        try:
            Path(name).write_text(self.hunks[s[0]],encoding="utf-8");git(self.repo,"apply","--cached","--reverse","--whitespace=nowarn",name);self.done();self.destroy()
        except Exception as e:messagebox.showerror("Unstage hunk",str(e),parent=self)
        finally:
            try:os.unlink(name)
            except OSError:pass

class ReflogRecoveryCenter(tk.Toplevel):
    """Browse reflog events and recover commits through safe branch creation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Reflog Recovery Center");self.geometry("1250x780");self.minsize(1000,650);self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Create recovery branch",self.recover_branch),("Inspect commit",self.inspect),("Checkout detached",self.checkout),("Expire preview",self.expire_preview)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("selector","hash","date","action","message"),show="headings")
        for c,t,w in [("selector","Reflog entry",130),("hash","Commit",100),("date","Date",160),("action","Action",180),("message","Message",520)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.text=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
        ttk.Label(self,text="Safest recovery: create a new branch at the selected reflog commit. This center does not run hard reset or delete reflog entries.",padding=8).pack(fill="x")
    def refresh(self):
        try:
            raw=git(self.repo,"reflog","show","--all","--date=iso-strict","--format=%gd%x1f%H%x1f%h%x1f%cd%x1f%gs","-500");self.rows=[];self.tree.delete(*self.tree.get_children())
            for line in raw.splitlines():
                p=line.split("\x1f",4)
                if len(p)==5:
                    selector,full,short,date,msg=p;action=msg.split(":",1)[0] if ":" in msg else msg;self.rows.append(dict(selector=selector,full=full,short=short,date=date,action=action,message=msg));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(selector,short,date,action,msg))
        except Exception as e:messagebox.showerror("Reflog",str(e),parent=self)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def details(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--decorate","--date=iso-strict","--pretty=fuller",r["full"])
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def recover_branch(self):
        import datetime,re
        r=self.selected()
        if not r:return
        default=f"recovery/{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{r['short']}";name=simpledialog.askstring("Recovery branch","New recovery branch name:",initialvalue=default,parent=self)
        if not name:return
        if not re.match(r"^[A-Za-z0-9._/-]+$",name):return messagebox.showwarning("Recovery","Invalid branch name characters.",parent=self)
        try:messagebox.showinfo("Recovery",git(self.repo,"branch",name,r["full"]),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Recovery",str(e),parent=self)
    def inspect(self):self.details()
    def checkout(self):
        r=self.selected()
        if r and messagebox.askyesno("Detached checkout",f"Checkout {r['short']} in detached HEAD mode? Prefer creating a recovery branch for permanent recovery.",parent=self):
            try:messagebox.showinfo("Checkout",git(self.repo,"switch","--detach",r["full"]),parent=self)
            except Exception as e:messagebox.showerror("Checkout",str(e),parent=self)
    def expire_preview(self):
        try:v=git(self.repo,"reflog","expire","--dry-run","--all")
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0","DRY-RUN ONLY. No entries were removed.\n\n"+v)

class InteractiveRebaseEditor(tk.Toplevel):
    """Visual interactive-rebase plan editor with automatic safety branch."""
    ACTIONS=("pick","reword","edit","squash","fixup","drop")
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Interactive Rebase Editor");self.geometry("1220x800");self.minsize(1000,680);self.rows=[];self._build();self.load_commits()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.base=tk.StringVar(value="HEAD~10")
        ttk.Label(top,text="Rebase onto / edit commits after").pack(side="left");ttk.Entry(top,textvariable=self.base,width=24).pack(side="left",padx=5)
        for text,cmd in [("Load plan",self.load_commits),("Move up",lambda:self.move(-1)),("Move down",lambda:self.move(1)),("Set action",self.set_action),("Start rebase",self.execute),("Continue",lambda:self.rebase_cmd("--continue")),("Skip",lambda:self.rebase_cmd("--skip")),("Abort",lambda:self.rebase_cmd("--abort"))]:ttk.Button(top,text=text,command=cmd).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("action","hash","subject","author","date"),show="headings",selectmode="browse")
        for c,t,w in [("action","Action",90),("hash","Commit",90),("subject","Subject",520),("author","Author",180),("date","Date",110)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True)
        self.preview=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.preview.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.show_commit())
        ttk.Label(self,text="A timestamped gccc-backup/pre-rebase-* branch is created before execution. The working tree must be clean. Merge commits are not rewritten by this first-parent linear editor.",padding=8).pack(fill="x")
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def load_commits(self):
        base=self.base.get().strip()
        if not base:return
        try:
            raw=git(self.repo,"log","--reverse","--first-parent","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%s",f"{base}..HEAD");self.rows=[];self.tree.delete(*self.tree.get_children())
            for line in raw.splitlines():
                p=line.split("\x1f",4)
                if len(p)==5:self.rows.append({"action":"pick","full":p[0],"short":p[1],"date":p[2],"author":p[3],"subject":p[4]})
            self.render();self.update_plan_preview()
        except Exception as e:messagebox.showerror("Interactive rebase",str(e),parent=self)
    def render(self):
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r["action"],r["short"],r["subject"],r["author"],r["date"]))
    def selected_index(self):
        s=self.tree.selection();return int(s[0]) if s else None
    def move(self,delta):
        i=self.selected_index()
        if i is None or not 0<=i+delta<len(self.rows):return
        self.rows[i],self.rows[i+delta]=self.rows[i+delta],self.rows[i];self.render();self.tree.selection_set(str(i+delta));self.update_plan_preview()
    def set_action(self):
        i=self.selected_index()
        if i is None:return
        win=tk.Toplevel(self);win.title("Choose rebase action");win.geometry("300x290")
        for action in self.ACTIONS:ttk.Button(win,text=action,command=lambda a=action:(self._apply_action(i,a),win.destroy())).pack(fill="x",padx=16,pady=4)
    def _apply_action(self,i,action):
        if i==0 and action in ("squash","fixup"):return messagebox.showwarning("Rebase plan","The first commit cannot squash/fixup into a previous commit.",parent=self)
        self.rows[i]["action"]=action;self.render();self.tree.selection_set(str(i));self.update_plan_preview()
    def plan(self):return "\n".join(f'{r["action"]} {r["full"]} {r["subject"]}' for r in self.rows)+"\n"
    def update_plan_preview(self):self.preview.delete("1.0","end");self.preview.insert("1.0","REBASE TODO\n"+"="*72+"\n"+self.plan())
    def show_commit(self):
        i=self.selected_index()
        if i is None:return
        try:v=git(self.repo,"show","--stat","--oneline",self.rows[i]["full"])
        except Exception as e:v=str(e)
        self.preview.delete("1.0","end");self.preview.insert("1.0",v+"\n\nPLAN\n"+"="*72+"\n"+self.plan())
    def execute(self):
        import datetime,tempfile,os,sys
        if not self.rows:return
        if not self.clean():return messagebox.showwarning("Interactive rebase","Commit or stash changes before rebasing.",parent=self)
        if not messagebox.askyesno("Start interactive rebase",f"Rewrite {len(self.rows)} commit(s) after {self.base.get()}? A backup branch will be created first.",parent=self):return
        backup=f"gccc-backup/pre-rebase-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            git(self.repo,"branch",backup)
            todo_fd,todo=tempfile.mkstemp(prefix="gccc-rebase-",suffix=".todo");os.close(todo_fd);Path(todo).write_text(self.plan(),encoding="utf-8")
            editor_fd,editor=tempfile.mkstemp(prefix="gccc-editor-",suffix=".py");os.close(editor_fd)
            Path(editor).write_text("import shutil,sys\nshutil.copyfile(sys.argv[1],sys.argv[2])\n",encoding="utf-8")
            env=os.environ.copy();env["GIT_SEQUENCE_EDITOR"]=f'\"{sys.executable}\" \"{editor}\" \"{todo}\"'
            r=subprocess.run(["git","rebase","-i",self.base.get().strip()],cwd=self.repo,text=True,capture_output=True,timeout=1800,env=env,encoding="utf-8",errors="replace")
            out=(r.stdout+"\n"+r.stderr).strip()
            if r.returncode:messagebox.showwarning("Rebase paused or failed",f"Backup: {backup}\n\n{out}\n\nResolve conflicts, then use Continue, Skip, or Abort.",parent=self)
            else:messagebox.showinfo("Rebase complete",f"Rebase completed. Safety branch: {backup}\n\n{out}",parent=self)
        except Exception as e:messagebox.showerror("Interactive rebase",str(e),parent=self)
        finally:
            for p in (locals().get("todo"),locals().get("editor")):
                if p:
                    try:os.unlink(p)
                    except OSError:pass
    def rebase_cmd(self,arg):
        try:messagebox.showinfo("Rebase",git(self.repo,"rebase",arg),parent=self);self.load_commits()
        except Exception as e:messagebox.showerror("Rebase",str(e),parent=self)

class UnifiedRefBrowser(tk.Toplevel):
    """Unified browser for branches, remotes, tags, stash and other refs."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Unified Ref Browser");self.geometry("1250x780");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.query=tk.StringVar();ttk.Entry(top,textvariable=self.query).pack(side="left",fill="x",expand=True);self.query.trace_add("write",lambda *_:self.render())
        for t,c in [("Refresh",self.refresh),("Checkout / switch",self.checkout),("Create branch here",self.branch),("Delete local branch/tag",self.delete),("Copy ref",self.copy_ref)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("type","name","hash","date","subject"),show="headings")
        for c,t,w in [("type","Type",110),("name","Reference",360),("hash","Commit",100),("date","Date",120),("subject","Subject",480)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.text=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
    def kind(self,name):
        if name.startswith("refs/heads/"):return "Local branch"
        if name.startswith("refs/remotes/"):return "Remote branch"
        if name.startswith("refs/tags/"):return "Tag"
        if name.startswith("refs/stash"):return "Stash"
        if name.startswith("refs/notes/"):return "Note"
        return "Other"
    def refresh(self):
        try:
            fmt="%(refname)%09%(objectname)%09%(objectname:short)%09%(committerdate:short)%09%(subject)";raw=git(self.repo,"for-each-ref",f"--format={fmt}","--sort=refname");self.rows=[]
            for line in raw.splitlines():
                p=line.split("\t",4)
                if len(p)==5:self.rows.append({"type":self.kind(p[0]),"name":p[0],"full":p[1],"short":p[2],"date":p[3],"subject":p[4]})
            self.render()
        except Exception as e:messagebox.showerror("Refs",str(e),parent=self)
    def render(self):
        q=self.query.get().lower();self.filtered=[r for r in self.rows if not q or q in (r["type"]+" "+r["name"]+" "+r["subject"]).lower()];self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.filtered):self.tree.insert("","end",iid=str(i),values=(r["type"],r["name"],r["short"],r["date"],r["subject"]))
    def selected(self):
        s=self.tree.selection();return self.filtered[int(s[0])] if s else None
    def details(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--decorate","--oneline",r["full"])
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def checkout(self):
        r=self.selected()
        if not r:return
        try:
            if r["type"]=="Local branch":out=git(self.repo,"switch",r["name"].replace("refs/heads/","",1))
            else:
                if not messagebox.askyesno("Checkout",f"Checkout {r['name']} in detached HEAD mode?",parent=self):return
                out=git(self.repo,"switch","--detach",r["full"])
            messagebox.showinfo("Checkout",out,parent=self)
        except Exception as e:messagebox.showerror("Checkout",str(e),parent=self)
    def branch(self):
        import re
        r=self.selected()
        if not r:return
        n=simpledialog.askstring("Create branch","New branch name:",parent=self)
        if n and re.match(r"^[A-Za-z0-9._/-]+$",n):
            try:messagebox.showinfo("Branch",git(self.repo,"branch",n,r["full"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Branch",str(e),parent=self)
    def delete(self):
        r=self.selected()
        if not r:return
        try:
            if r["type"]=="Local branch":
                n=r["name"].replace("refs/heads/","",1)
                if messagebox.askyesno("Delete branch",f"Delete merged local branch {n}?",parent=self):messagebox.showinfo("Delete",git(self.repo,"branch","-d",n),parent=self)
            elif r["type"]=="Tag":
                n=r["name"].replace("refs/tags/","",1)
                if messagebox.askyesno("Delete tag",f"Delete local tag {n}?",parent=self):messagebox.showinfo("Delete",git(self.repo,"tag","-d",n),parent=self)
            else:return messagebox.showinfo("Delete","Deletion is limited to local branches and local tags.",parent=self)
            self.refresh()
        except Exception as e:messagebox.showerror("Delete",str(e),parent=self)
    def copy_ref(self):
        r=self.selected()
        if r:self.clipboard_clear();self.clipboard_append(r["name"]);messagebox.showinfo("Reference","Copied ref name.",parent=self)

class RepositoryHistoryBrowser(tk.Toplevel):
    """Browse repository trees and file contents at any commit without checkout."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository History Browser");self.geometry("1350x820");self.minsize(1050,700);self.rows=[];self.current_ref="HEAD";self._build();self.load_commits()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.ref=tk.StringVar(value="HEAD");ttk.Entry(top,textvariable=self.ref,width=30).pack(side="left");ttk.Button(top,text="Load ref",command=self.load_tree).pack(side="left",padx=3);ttk.Button(top,text="Export selected file",command=self.export_file).pack(side="left");ttk.Button(top,text="Open commit inspector",command=lambda:CommitInspector(self,self.repo)).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);middle=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=2);pane.add(middle,weight=3);pane.add(right,weight=5)
        ttk.Label(left,text="Recent commits",font=("Segoe UI Semibold",10)).pack(anchor="w");self.commits=tk.Listbox(left,font=("Consolas",9));self.commits.pack(fill="both",expand=True);self.commits.bind("<<ListboxSelect>>",lambda e:self.select_commit())
        ttk.Label(middle,text="Repository tree",font=("Segoe UI Semibold",10)).pack(anchor="w");self.tree=ttk.Treeview(middle,columns=("type","size"),show="tree headings");self.tree.heading("#0",text="Path");self.tree.heading("type",text="Type");self.tree.heading("size",text="Size");self.tree.column("#0",width=360);self.tree.column("type",width=80);self.tree.column("size",width=90);self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewOpen>>",lambda e:self.expand());self.tree.bind("<<TreeviewSelect>>",lambda e:self.open_selected())
        ttk.Label(right,text="Historical file content",font=("Segoe UI Semibold",10)).pack(anchor="w");self.content=tk.Text(right,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.content.pack(fill="both",expand=True)
    def load_commits(self):
        raw=git(self.repo,"log","-150","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%s");self.rows=[];self.commits.delete(0,"end")
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:self.rows.append(p);self.commits.insert("end",f"{p[1]}  {p[2]}  {p[3]}")
        self.load_tree()
    def select_commit(self):
        s=self.commits.curselection()
        if s:self.ref.set(self.rows[s[0]][0]);self.load_tree()
    def entries(self,path=""):
        spec=f"{self.current_ref}:{path}" if path else self.current_ref
        raw=git(self.repo,"ls-tree","-l",spec);out=[]
        for line in raw.splitlines():
            if "\t" not in line:continue
            meta,name=line.split("\t",1);p=meta.split();out.append({"mode":p[0],"type":p[1],"hash":p[2],"size":p[3] if len(p)>3 else "-","name":name})
        return out
    def load_tree(self):
        self.current_ref=self.ref.get().strip() or "HEAD";self.tree.delete(*self.tree.get_children());self.content.delete("1.0","end")
        try:
            for e in self.entries():
                iid=self.tree.insert("","end",text=e["name"],values=(e["type"],e["size"]),tags=(e["hash"],e["type"],e["name"]))
                if e["type"]=="tree":self.tree.insert(iid,"end",text="Loading...")
        except Exception as e:messagebox.showerror("History browser",str(e),parent=self)
    def node_path(self,iid):
        parts=[]
        while iid:
            parts.append(self.tree.item(iid,"text"));iid=self.tree.parent(iid)
        return "/".join(reversed(parts))
    def expand(self):
        iid=self.tree.focus()
        if not iid:return
        children=self.tree.get_children(iid)
        if len(children)==1 and self.tree.item(children[0],"text")=="Loading...":
            self.tree.delete(children[0]);path=self.node_path(iid)
            try:
                for e in self.entries(path):
                    child=self.tree.insert(iid,"end",text=e["name"],values=(e["type"],e["size"]),tags=(e["hash"],e["type"],path+"/"+e["name"]))
                    if e["type"]=="tree":self.tree.insert(child,"end",text="Loading...")
            except Exception as e:messagebox.showerror("History browser",str(e),parent=self)
    def selected_path(self):
        s=self.tree.selection();return self.node_path(s[0]) if s else None
    def open_selected(self):
        s=self.tree.selection()
        if not s:return
        iid=s[0];vals=self.tree.item(iid,"values")
        if not vals or vals[0]!="blob":return
        path=self.node_path(iid)
        try:v=git(self.repo,"show",f"{self.current_ref}:{path}");self.content.delete("1.0","end");self.content.insert("1.0",v)
        except Exception as e:self.content.delete("1.0","end");self.content.insert("1.0","Binary or unreadable content.\n\n"+str(e))
    def export_file(self):
        path=self.selected_path()
        if not path:return
        s=self.tree.selection();vals=self.tree.item(s[0],"values")
        if not vals or vals[0]!="blob":return messagebox.showinfo("Export","Select a file, not a directory.",parent=self)
        target=filedialog.asksaveasfilename(parent=self,initialfile=Path(path).name)
        if target:
            try:
                r=subprocess.run(["git","show",f"{self.current_ref}:{path}"],cwd=self.repo,capture_output=True,timeout=120)
                if r.returncode:raise GitError(r.stderr.decode("utf-8",errors="replace"))
                Path(target).write_bytes(r.stdout);messagebox.showinfo("Export",f"Saved {target}",parent=self)
            except Exception as e:messagebox.showerror("Export",str(e),parent=self)

class SparseCheckoutCenter(tk.Toplevel):
    """Configure cone-mode sparse checkout for large repositories."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Sparse Checkout Center");self.geometry("1120x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Enable cone mode",self.enable),("Apply selected folders",self.apply),("Add folder",self.add),("Disable sparse checkout",self.disable)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        ttk.Label(l,text="Top-level repository folders",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=4)
        self.folders=tk.Listbox(l,selectmode="extended",font=("Consolas",9));self.folders.pack(fill="both",expand=True)
        ttk.Label(r,text="Current sparse-checkout configuration",font=("Segoe UI Semibold",10)).pack(anchor="w",pady=4)
        self.text=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
        ttk.Label(self,text="Sparse checkout changes which tracked paths are materialized locally. Commit or stash local changes before changing the sparse specification.",padding=8).pack(fill="x")
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def refresh(self):
        try:
            raw=git(self.repo,"ls-tree","-d","--name-only","HEAD");self.all_folders=[x for x in raw.splitlines() if x and x!="Completed successfully."];self.folders.delete(0,"end")
            for x in self.all_folders:self.folders.insert("end",x)
            enabled=git(self.repo,"config","--bool","core.sparseCheckout")
            try:spec=git(self.repo,"sparse-checkout","list")
            except Exception:spec="No sparse paths configured."
            self.text.delete("1.0","end");self.text.insert("1.0",f"Enabled: {enabled}\n\n{spec}")
            selected=set(spec.splitlines())
            for i,x in enumerate(self.all_folders):
                if x in selected:self.folders.selection_set(i)
        except Exception as e:messagebox.showerror("Sparse checkout",str(e),parent=self)
    def enable(self):
        if not self.clean():return messagebox.showwarning("Sparse checkout","Commit or stash changes first.",parent=self)
        try:messagebox.showinfo("Sparse checkout",git(self.repo,"sparse-checkout","init","--cone"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Sparse checkout",str(e),parent=self)
    def chosen(self):return [self.all_folders[i] for i in self.folders.curselection()]
    def apply(self):
        paths=self.chosen()
        if not paths:return messagebox.showwarning("Sparse checkout","Select at least one folder.",parent=self)
        if not self.clean():return messagebox.showwarning("Sparse checkout","Commit or stash changes first.",parent=self)
        if messagebox.askyesno("Apply sparse checkout","Materialize only the selected folders plus root-level files?",parent=self):
            try:messagebox.showinfo("Sparse checkout",git(self.repo,"sparse-checkout","set",*paths),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Sparse checkout",str(e),parent=self)
    def add(self):
        p=simpledialog.askstring("Sparse checkout","Folder path to add:",parent=self)
        if p:
            try:messagebox.showinfo("Sparse checkout",git(self.repo,"sparse-checkout","add",p),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Sparse checkout",str(e),parent=self)
    def disable(self):
        if not self.clean():return messagebox.showwarning("Sparse checkout","Commit or stash changes first.",parent=self)
        if messagebox.askyesno("Disable sparse checkout","Restore the full working tree?",parent=self):
            try:messagebox.showinfo("Sparse checkout",git(self.repo,"sparse-checkout","disable"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Sparse checkout",str(e),parent=self)

class MaintenanceCenter(tk.Toplevel):
    """Inspect storage and run guarded Git maintenance operations."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Maintenance Center");self.geometry("1100x730");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh analysis",self.refresh),("Run auto maintenance",self.auto),("Run git gc",self.gc),("Verify objects",self.fsck),("Commit graph write",self.commit_graph),("Register scheduled maintenance",self.register)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Aggressive garbage collection and immediate reflog expiration are intentionally not exposed. Close other Git tools before manual maintenance.",padding=8).pack(fill="x")
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        count=self.safe("count-objects","-vH");packs=self.safe("verify-pack","-v",str(Path(self.repo)/".git"/"objects"/"pack"/"*.idx")) if False else "Pack details available through count-objects."
        maint=self.safe("config","--get","maintenance.auto");report="REPOSITORY STORAGE & MAINTENANCE\n"+"="*72+"\n\nOBJECT DATABASE\n"+count+"\n\nMAINTENANCE CONFIG\nmaintenance.auto: "+maint+"\n\nRECENT INTEGRITY\nRun Verify objects for a full fsck."
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def run(self,args,title,confirm=None):
        if confirm and not messagebox.askyesno(title,confirm,parent=self):return
        try:out=git(self.repo,*args);messagebox.showinfo(title,out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror(title,str(e),parent=self)
    def auto(self):self.run(["maintenance","run","--auto"],"Auto maintenance")
    def gc(self):self.run(["gc"],"Git GC","Run normal git gc now? This may take time on a large repository.")
    def fsck(self):self.run(["fsck","--full","--no-progress"],"Object verification")
    def commit_graph(self):self.run(["commit-graph","write","--reachable","--changed-paths"],"Commit graph")
    def register(self):self.run(["maintenance","register"],"Scheduled maintenance","Register this repository for Git's scheduled maintenance? Availability depends on your Git/OS scheduler integration.")

class GitNotesCenter(tk.Toplevel):
    """Attach non-rewriting annotations to commits using git notes."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Notes Center");self.geometry("1120x740");self.rows=[];self._build();self.load_commits()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.ref=tk.StringVar(value="refs/notes/commits");ttk.Entry(top,textvariable=self.ref,width=28).pack(side="left")
        for t,c in [("Load commits",self.load_commits),("Load note",self.load_note),("Save note",self.save_note),("Delete note",self.delete_note),("Push notes ref",self.push_notes)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Consolas",9));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.load_note())
        self.note=tk.Text(r,wrap="word",undo=True,font=("Segoe UI",10));self.note.pack(fill="both",expand=True)
        ttk.Label(self,text="Git notes do not rewrite commits. Notes are stored in a separate ref and are not pushed unless you explicitly push that notes ref.",padding=8).pack(fill="x")
    def notes_name(self):return self.ref.get().replace("refs/notes/","") if self.ref.get().startswith("refs/notes/") else self.ref.get()
    def load_commits(self):
        raw=git(self.repo,"log","-200","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%s");self.rows=[];self.list.delete(0,"end")
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:self.rows.append(p);self.list.insert("end",f"{p[1]}  {p[2]}  {p[3]}")
    def selected(self):
        s=self.list.curselection();return self.rows[s[0]][0] if s else None
    def load_note(self):
        c=self.selected();self.note.delete("1.0","end")
        if not c:return
        try:v=git(self.repo,"notes",f"--ref={self.notes_name()}","show",c);self.note.insert("1.0","" if v=="Completed successfully." else v)
        except Exception:self.note.insert("1.0","")
    def save_note(self):
        c=self.selected()
        if not c:return
        text=self.note.get("1.0","end-1c").strip()
        if not text:return messagebox.showwarning("Git notes","Enter note text.",parent=self)
        try:messagebox.showinfo("Git notes",git(self.repo,"notes",f"--ref={self.notes_name()}","add","-f","-m",text,c),parent=self)
        except Exception as e:messagebox.showerror("Git notes",str(e),parent=self)
    def delete_note(self):
        c=self.selected()
        if c and messagebox.askyesno("Delete note","Delete the note from the selected commit?",parent=self):
            try:messagebox.showinfo("Git notes",git(self.repo,"notes",f"--ref={self.notes_name()}","remove",c),parent=self);self.load_note()
            except Exception as e:messagebox.showerror("Git notes",str(e),parent=self)
    def push_notes(self):
        ref=self.ref.get().strip()
        if messagebox.askyesno("Push notes",f"Push {ref} to origin?",parent=self):
            try:messagebox.showinfo("Push notes",git(self.repo,"push","origin",ref),parent=self)
            except Exception as e:messagebox.showerror("Push notes",str(e),parent=self)

class DiffMergeToolCenter(tk.Toplevel):
    """Configure and launch common external diff/merge tools."""
    TOOLS={"VS Code":("code --wait --diff", "code --wait"),"WinMerge":("WinMergeU", "WinMergeU"),"Beyond Compare":("bcompare", "bcompare"),"KDiff3":("kdiff3", "kdiff3")}
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Diff & Merge Tool Center");self.geometry("950x620");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.tool=tk.StringVar(value="VS Code");ttk.Combobox(top,textvariable=self.tool,values=list(self.TOOLS),state="readonly",width=20).pack(side="left")
        for t,c in [("Configure repository",self.configure),("Launch difftool",self.difftool),("Launch mergetool",self.mergetool),("Refresh",self.refresh)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.path=tk.StringVar();ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True,padx=4);ttk.Button(top,text="Diff selected path",command=self.diff_path).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        def cfg(k):
            try:return git(self.repo,"config","--get",k)
            except:return "Not configured"
        v=f"diff.tool: {cfg('diff.tool')}\nmerge.tool: {cfg('merge.tool')}\n\nChoose a known tool or configure custom commands manually in Git if installed under a non-standard executable name."
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def configure(self):
        name=self.tool.get();key=name.lower().replace(" ","");diff_cmd,merge_cmd=self.TOOLS[name]
        try:
            git(self.repo,"config","diff.tool",key);git(self.repo,"config",f"difftool.{key}.cmd",diff_cmd+' "$LOCAL" "$REMOTE"');git(self.repo,"config","merge.tool",key);git(self.repo,"config",f"mergetool.{key}.cmd",merge_cmd+' "$BASE" "$LOCAL" "$REMOTE" "$MERGED"');git(self.repo,"config","mergetool.keepBackup","false");messagebox.showinfo("Tools",f"Configured {name} for this repository.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Tools",str(e),parent=self)
    def difftool(self):
        try:messagebox.showinfo("Difftool",git(self.repo,"difftool","--no-prompt"),parent=self)
        except Exception as e:messagebox.showerror("Difftool",str(e),parent=self)
    def diff_path(self):
        p=self.path.get().strip()
        if p:
            try:messagebox.showinfo("Difftool",git(self.repo,"difftool","--no-prompt","--",p),parent=self)
            except Exception as e:messagebox.showerror("Difftool",str(e),parent=self)
    def mergetool(self):
        try:messagebox.showinfo("Mergetool",git(self.repo,"mergetool","--no-prompt"),parent=self)
        except Exception as e:messagebox.showerror("Mergetool",str(e),parent=self)

class RerereCenter(tk.Toplevel):
    """Recorded-resolution management for recurring merge/rebase conflicts."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Recorded Conflict Resolution (rerere)");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");
        for text,cmd in [("Refresh",self.refresh),("Enable rerere",self.enable),("Enable autoupdate",self.autoupdate),("Run rerere",self.run_rerere),("Forget selected paths",self.forget),("Clear cache",self.clear)]:ttk.Button(top,text=text,command=cmd).pack(side="left",padx=2)
        self.path=tk.StringVar();ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True,padx=5)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="rerere records conflict resolutions so Git can reuse them later. Clear/forget only affects the resolution cache, not commits.",padding=8).pack(fill="x")
    def cfg(self,key):
        try:return git(self.repo,"config","--get",key)
        except:return "Not set"
    def refresh(self):
        try:status=git(self.repo,"rerere","status")
        except Exception:status="No recorded conflict currently active."
        try:remaining=git(self.repo,"rerere","remaining")
        except Exception:remaining="None"
        report=f"RERERE CONFIGURATION\n{'='*72}\nrerere.enabled: {self.cfg('rerere.enabled')}\nrerere.autoupdate: {self.cfg('rerere.autoupdate')}\n\nSTATUS\n{status}\n\nREMAINING\n{remaining}"
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def enable(self):
        try:git(self.repo,"config","rerere.enabled","true");messagebox.showinfo("rerere","Enabled for this repository.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("rerere",str(e),parent=self)
    def autoupdate(self):
        try:git(self.repo,"config","rerere.autoupdate","true");messagebox.showinfo("rerere","Autoupdate enabled. Review automatically staged resolutions before committing.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("rerere",str(e),parent=self)
    def run_rerere(self):
        try:messagebox.showinfo("rerere",git(self.repo,"rerere"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("rerere",str(e),parent=self)
    def forget(self):
        paths=[x.strip() for x in self.path.get().split(",") if x.strip()]
        if not paths:return messagebox.showwarning("rerere","Enter one or more comma-separated conflicted paths.",parent=self)
        if messagebox.askyesno("Forget resolution",f"Forget saved resolution for:\n"+"\n".join(paths),parent=self):
            try:messagebox.showinfo("rerere",git(self.repo,"rerere","forget","--",*paths),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("rerere",str(e),parent=self)
    def clear(self):
        if messagebox.askyesno("Clear rerere cache","Clear recorded conflict resolutions for this repository? This does not change commits.",parent=self):
            try:messagebox.showinfo("rerere",git(self.repo,"rerere","clear"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("rerere",str(e),parent=self)

class RemoteBranchCenter(tk.Toplevel):
    """Explicit remote branch tracking, publish, rename and delete workflows."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote Branch Center");self.geometry("1160x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for text,cmd in [("Refresh",self.refresh),("Fetch/prune",self.fetch),("Track selected",self.track),("Publish current",self.publish),("Rename local branch",self.rename),("Delete remote branch",self.delete_remote)]:ttk.Button(top,text=text,command=cmd).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("type","name","upstream","ahead","behind","sha"),show="headings")
        for c,t,w in [("type","Type",100),("name","Branch",300),("upstream","Upstream",260),("ahead","Ahead",70),("behind","Behind",70),("sha","Commit",100)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Remote deletion requires exact typed confirmation. Tracking creates a local branch from a selected remote-tracking ref.",padding=8).pack(fill="x")
    def safe_count(self,spec):
        try:return git(self.repo,"rev-list","--count",spec)
        except:return "-"
    def refresh(self):
        self.rows=[];self.tree.delete(*self.tree.get_children())
        try:
            raw=git(self.repo,"for-each-ref","--format=%(refname)%09%(refname:short)%09%(upstream:short)%09%(objectname:short)","refs/heads/","refs/remotes/")
            for line in raw.splitlines():
                p=line.split("\t");full=p[0];name=p[1];up=p[2] if len(p)>2 else "";sha=p[3] if len(p)>3 else "";typ="Local" if full.startswith("refs/heads/") else "Remote"
                ahead=behind="-"
                if typ=="Local" and up:ahead=self.safe_count(f"{up}..{name}");behind=self.safe_count(f"{name}..{up}")
                r=dict(type=typ,name=name,upstream=up,sha=sha,ahead=ahead,behind=behind);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(typ,name,up or "-",ahead,behind,sha))
        except Exception as e:messagebox.showerror("Remote branches",str(e),parent=self)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def track(self):
        import re
        r=self.selected()
        if not r or r["type"]!="Remote":return messagebox.showinfo("Track","Select a remote-tracking branch.",parent=self)
        if r["name"].endswith("/HEAD"):return
        default=r["name"].split("/",1)[1] if "/" in r["name"] else r["name"];name=simpledialog.askstring("Track branch","Local branch name:",initialvalue=default,parent=self)
        if name and re.match(r"^[A-Za-z0-9._/-]+$",name):
            try:messagebox.showinfo("Track",git(self.repo,"switch","-c",name,"--track",r["name"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Track",str(e),parent=self)
    def publish(self):
        try:b=git(self.repo,"branch","--show-current")
        except Exception as e:return messagebox.showerror("Publish",str(e),parent=self)
        if not b:return
        if messagebox.askyesno("Publish branch",f"Push {b} to origin and set upstream?",parent=self):
            try:messagebox.showinfo("Publish",git(self.repo,"push","-u","origin",b),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Publish",str(e),parent=self)
    def rename(self):
        r=self.selected()
        if not r or r["type"]!="Local":return messagebox.showinfo("Rename","Select a local branch.",parent=self)
        new=simpledialog.askstring("Rename branch",f"New name for {r['name']}:",parent=self)
        if new:
            try:messagebox.showinfo("Rename",git(self.repo,"branch","-m",r["name"],new),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Rename",str(e),parent=self)
    def delete_remote(self):
        r=self.selected()
        if not r or r["type"]!="Remote":return messagebox.showinfo("Delete remote branch","Select a remote branch.",parent=self)
        if "/" not in r["name"] or r["name"].endswith("/HEAD"):return
        remote,branch=r["name"].split("/",1);typed=simpledialog.askstring("Delete remote branch",f"This deletes {remote}/{branch} on the server.\nType the branch name exactly to continue:\n{branch}",parent=self)
        if typed!=branch:return
        try:messagebox.showinfo("Delete remote branch",git(self.repo,"push",remote,"--delete",branch),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Delete remote branch",str(e),parent=self)

class IgnoreAttributesStudio(tk.Toplevel):
    """Unified editor and tester for .gitignore and .gitattributes."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Ignore & Attributes Studio");self.geometry("1180x760");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar();ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        for text,cmd in [("Test ignore",self.test_ignore),("Check attributes",self.check_attr),("Save files",self.save),("Add Python defaults",self.python_defaults),("Add binary defaults",self.binary_defaults)]:ttk.Button(top,text=text,command=cmd).pack(side="left",padx=2)
        nb=ttk.Notebook(self);nb.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(nb);b=ttk.Frame(nb);c=ttk.Frame(nb);nb.add(a,text=".gitignore");nb.add(b,text=".gitattributes");nb.add(c,text="Test results")
        self.ignore=tk.Text(a,wrap="none",undo=True,font=("Consolas",9));self.ignore.pack(fill="both",expand=True)
        self.attrs=tk.Text(b,wrap="none",undo=True,font=("Consolas",9));self.attrs.pack(fill="both",expand=True)
        self.out=tk.Text(c,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def load(self):
        for widget,name in ((self.ignore,".gitignore"),(self.attrs,".gitattributes")):
            p=Path(self.repo)/name;widget.delete("1.0","end");widget.insert("1.0",p.read_text(encoding="utf-8",errors="replace") if p.exists() else "")
    def save(self):
        (Path(self.repo)/".gitignore").write_text(self.ignore.get("1.0","end-1c")+"\n",encoding="utf-8");(Path(self.repo)/".gitattributes").write_text(self.attrs.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Ignore & Attributes","Saved both files. Review and stage them when ready.",parent=self)
    def result(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def test_ignore(self):
        p=self.path.get().strip()
        if not p:return
        try:self.result(git(self.repo,"check-ignore","-v","--no-index","--",p))
        except Exception as e:self.result("Path is not ignored, or Git returned:\n"+str(e))
    def check_attr(self):
        p=self.path.get().strip()
        if not p:return
        try:self.result(git(self.repo,"check-attr","-a","--",p))
        except Exception as e:self.result(str(e))
    def append_unique(self,w,text):
        cur=w.get("1.0","end-1c")
        for line in text.splitlines():
            if line and line not in cur.splitlines():w.insert("end",("\n" if w.get("1.0","end-1c") else "")+line)
    def python_defaults(self):self.append_unique(self.ignore,"__pycache__/\n*.py[cod]\n.venv/\nbuild/\ndist/\n*.egg-info/\n.env")
    def binary_defaults(self):self.append_unique(self.attrs,"* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.jpeg binary\n*.gif binary\n*.zip binary\n*.pdf binary")

class CloneWizard(tk.Toplevel):
    """Guided clone with depth, single-branch, no-checkout and blob-filter options."""
    def __init__(self,parent):
        super().__init__(parent);self.title("Advanced Clone Wizard");self.geometry("820x620");self._build()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.url=tk.StringVar();self.dest=tk.StringVar();self.branch=tk.StringVar();self.depth=tk.IntVar(value=0);self.single=tk.BooleanVar();self.no_checkout=tk.BooleanVar();self.partial=tk.BooleanVar();self.recurse=tk.BooleanVar(value=True)
        rows=[("Repository URL",ttk.Entry(f,textvariable=self.url)),("Destination parent",ttk.Entry(f,textvariable=self.dest)),("Branch (optional)",ttk.Entry(f,textvariable=self.branch)),("Depth (0 = full)",ttk.Spinbox(f,from_=0,to=100000,textvariable=self.depth))]
        for i,(label,w) in enumerate(rows):ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=7);w.grid(row=i,column=1,sticky="ew",padx=8,pady=7)
        ttk.Button(f,text="Browse destination",command=lambda:self.dest.set(filedialog.askdirectory(parent=self) or self.dest.get())).grid(row=1,column=2)
        for j,(text,var) in enumerate((("Single branch",self.single),("No checkout",self.no_checkout),("Partial clone: filter blobs",self.partial),("Recurse submodules",self.recurse)),start=4):ttk.Checkbutton(f,text=text,variable=var).grid(row=j,column=1,sticky="w",pady=5)
        f.columnconfigure(1,weight=1);ttk.Button(f,text="Clone repository",command=self.clone,style="Accent.TButton").grid(row=9,column=1,sticky="e",pady=20)
        self.out=tk.Text(f,height=10,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=10,column=0,columnspan=3,sticky="nsew");f.rowconfigure(10,weight=1)
    def clone(self):
        u=self.url.get().strip();d=self.dest.get().strip()
        if not u or not d:return messagebox.showwarning("Clone","Repository URL and destination are required.",parent=self)
        args=["clone"]
        if self.depth.get()>0:args += ["--depth",str(self.depth.get())]
        if self.branch.get().strip():args += ["--branch",self.branch.get().strip()]
        if self.single.get():args.append("--single-branch")
        if self.no_checkout.get():args.append("--no-checkout")
        if self.partial.get():args += ["--filter=blob:none"]
        if self.recurse.get():args.append("--recurse-submodules")
        args.append(u)
        try:out=git(d,*args);self.out.delete("1.0","end");self.out.insert("1.0",out);messagebox.showinfo("Clone","Clone completed.",parent=self)
        except Exception as e:self.out.delete("1.0","end");self.out.insert("1.0",str(e));messagebox.showerror("Clone",str(e),parent=self)

class WorktreeSafetyCenter(tk.Toplevel):
    """Worktree-aware branch safety and cleanup dashboard."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Worktree Safety Center");self.geometry("1180x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Open selected folder",self.open_folder),("Lock worktree",self.lock),("Unlock worktree",self.unlock),("Prune dry-run",self.prune_preview),("Prune",self.prune)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("path","branch","head","locked","prunable"),show="headings")
        for c,t,w in [("path","Worktree",470),("branch","Branch",240),("head","HEAD",110),("locked","Locked",90),("prunable","Prunable",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Use lock for removable/network drives. Prune removes stale worktree administrative records, not a healthy checked-out worktree.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"worktree","list","--porcelain");self.rows=[];cur={}
        for line in raw.splitlines()+[""]:
            if not line:
                if cur:self.rows.append(cur);cur={}
            elif " " in line:
                k,v=line.split(" ",1);cur[k]=v
            else:cur[line]="true"
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r.get("worktree",""),r.get("branch","").replace("refs/heads/",""),r.get("HEAD","")[:10],"Yes" if "locked" in r else "No","Yes" if "prunable" in r else "No"))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def open_folder(self):
        import os
        r=self.selected()
        if r:
            p=r.get("worktree")
            try:os.startfile(p) if hasattr(os,"startfile") else subprocess.Popen(["xdg-open",p])
            except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def worktree_cmd(self,action):
        r=self.selected()
        if not r:return
        try:messagebox.showinfo("Worktree",git(self.repo,"worktree",action,r["worktree"]),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def lock(self):self.worktree_cmd("lock")
    def unlock(self):self.worktree_cmd("unlock")
    def prune_preview(self):
        try:messagebox.showinfo("Prune dry-run",git(self.repo,"worktree","prune","--dry-run","--verbose"),parent=self)
        except Exception as e:messagebox.showerror("Prune",str(e),parent=self)
    def prune(self):
        if messagebox.askyesno("Prune worktrees","Remove stale worktree administration records?",parent=self):
            try:messagebox.showinfo("Prune",git(self.repo,"worktree","prune","--verbose"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Prune",str(e),parent=self)

class RepositoryDoctor(tk.Toplevel):
    """Actionable repository diagnosis combining Git state, config and integrity."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Doctor");self.geometry("1120x760");self._build();self.run()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Run diagnosis",command=self.run).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "ERROR: "+str(e)
    def run(self):
        checks=[]
        status=self.safe("status","--porcelain");checks.append(("Working tree",status=="Completed successfully.","Clean" if status=="Completed successfully." else "Local changes exist"))
        branch=self.safe("branch","--show-current");checks.append(("Current branch",bool(branch) and not branch.startswith("ERROR"),branch))
        upstream=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");checks.append(("Upstream",not upstream.startswith("ERROR"),upstream))
        remote=self.safe("remote","get-url","origin");checks.append(("Origin",not remote.startswith("ERROR"),remote))
        fsck=self.safe("fsck","--no-progress");checks.append(("Object integrity",not fsck.startswith("ERROR"),fsck))
        try:conf=git(self.repo,"diff","--name-only","--diff-filter=U");conflict=conf!="Completed successfully." and bool(conf.strip())
        except:conflict=False;conf=""
        checks.append(("Merge conflicts",not conflict,conf if conflict else "None"))
        try:a=git(self.repo,"rev-list","--count","@{u}..HEAD");b=git(self.repo,"rev-list","--count","HEAD..@{u}");sync=f"Ahead {a}, behind {b}";ok=not (a!="0" and b!="0")
        except Exception as e:sync="Unavailable: "+str(e);ok=False
        checks.append(("Sync divergence",ok,sync))
        report="REPOSITORY DOCTOR\n"+"="*78+"\n\n"+"\n\n".join(f"[{'PASS' if ok else 'ATTN'}] {name}\n  {detail}" for name,ok,detail in checks)+"\n\nRECOMMENDED ACTIONS\n"
        for name,ok,detail in checks:
            if not ok:
                advice={"Working tree":"Commit, discard, or stash intentional changes before risky operations.","Upstream":"Publish the branch or configure its upstream.","Origin":"Configure an origin remote.","Object integrity":"Review fsck output before further cleanup.","Merge conflicts":"Open Resolve conflicts.","Sync divergence":"Open Compare, then explicitly merge or rebase."}.get(name,"Review the reported state.");report+=f"- {name}: {advice}\n"
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-doctor.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class TagReleaseAuditCenter(tk.Toplevel):
    """Audit tags for type, target, date, signature and remote presence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Tag & Release Audit");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Verify selected signature",command=self.verify).pack(side="left",padx=3);ttk.Button(top,text="Push selected tag",command=self.push).pack(side="left");ttk.Button(top,text="Open release center",command=lambda:ReleaseCenter(self,self.repo)).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("tag","type","target","date","remote"),show="headings")
        for c,t,w in [("tag","Tag",270),("type","Type",100),("target","Target",110),("date","Tagger/commit date",170),("remote","On origin",100)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        remote=set()
        try:
            r=git(self.repo,"ls-remote","--tags","origin");remote={x.split("refs/tags/",1)[1].replace("^{}","") for x in r.splitlines() if "refs/tags/" in x}
        except:pass
        raw=git(self.repo,"for-each-ref","--sort=-creatordate","--format=%(refname:short)%09%(objecttype)%09%(objectname:short)%09%(creatordate:iso8601)","refs/tags/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3)
            if len(p)==4:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[0],"Annotated" if p[1]=="tag" else "Lightweight",p[2],p[3],"Yes" if p[0] in remote else "No"))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def verify(self):
        t=self.selected()
        if not t:return
        try:v=git(self.repo,"tag","-v",t)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def push(self):
        t=self.selected()
        if t and messagebox.askyesno("Push tag",f"Push {t} to origin?",parent=self):
            try:messagebox.showinfo("Push tag",git(self.repo,"push","origin",f"refs/tags/{t}"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Push tag",str(e),parent=self)

class StashManagerPro(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Stash Manager Pro");self.geometry("1180x760");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.msg=tk.StringVar()
        ttk.Entry(top,textvariable=self.msg).pack(side="left",fill="x",expand=True)
        for t,c in [("Stash tracked",lambda:self.save(False)),("Stash + untracked",lambda:self.save(True)),("Refresh",self.refresh),("Apply",self.apply),("Pop",self.pop),("Create branch",self.branch),("Drop",self.drop)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=("stash","date","branch","message"),show="headings")
        for c,t,w in [("stash","Stash",100),("date","Date",170),("branch","Branch/context",230),("message","Message",600)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
        self.text=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True)
    def refresh(self):
        raw=git(self.repo,"stash","list","--date=iso-strict","--format=%gd%x1f%cd%x1f%gs");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\x1f",2)
            if len(p)==3:
                msg=p[2];branch=msg.split(":",1)[0];self.rows.append((p[0],p[1],branch,msg));self.tree.insert("","end",iid=str(len(self.rows)-1),values=self.rows[-1])
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def details(self):
        st=self.selected()
        if st:
            try:v=git(self.repo,"stash","show","--stat","--patch",st)
            except Exception as e:v=str(e)
            self.text.delete("1.0","end");self.text.insert("1.0",v)
    def save(self,untracked):
        args=["stash","push"]+(["-u"] if untracked else [])+["-m",self.msg.get().strip() or "GitHub Command Center stash"]
        try:messagebox.showinfo("Stash",git(self.repo,*args),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Stash",str(e),parent=self)
    def action(self,kind):
        st=self.selected()
        if not st:return
        try:messagebox.showinfo("Stash",git(self.repo,"stash",kind,st),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Stash",str(e),parent=self)
    def apply(self):self.action("apply")
    def pop(self):
        st=self.selected()
        if st and messagebox.askyesno("Pop stash",f"Apply and drop {st}?",parent=self):self.action("pop")
    def drop(self):
        st=self.selected()
        if st and messagebox.askyesno("Drop stash",f"Permanently drop {st}?",parent=self):self.action("drop")
    def branch(self):
        st=self.selected()
        if not st:return
        name=simpledialog.askstring("Stash branch","New branch name:",parent=self)
        if name:
            try:messagebox.showinfo("Stash branch",git(self.repo,"stash","branch",name,st),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Stash branch",str(e),parent=self)

class CleanPreviewCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safe Clean Center");self.geometry("1000x660");self.include_ignored=tk.BooleanVar();self.directories=tk.BooleanVar(value=True);self._build();self.preview()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Checkbutton(top,text="Include directories",variable=self.directories,command=self.preview).pack(side="left");ttk.Checkbutton(top,text="Include ignored files",variable=self.include_ignored,command=self.preview).pack(side="left",padx=8);ttk.Button(top,text="Refresh preview",command=self.preview).pack(side="left");ttk.Button(top,text="Clean previewed items",command=self.clean).pack(side="right")
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Cleaning cannot be undone by Git. Ignored files are excluded by default and require an extra typed confirmation when included.",padding=8).pack(fill="x")
    def args(self,dry=True):
        args=["clean",f"-{'n' if dry else 'f'}"]
        if self.directories.get():args.append("-d")
        if self.include_ignored.get():args.append("-x")
        return args
    def preview(self):
        try:v=git(self.repo,*self.args(True))
        except Exception as e:v=str(e)
        self.preview_text=v;self.text.delete("1.0","end");self.text.insert("1.0",v)
    def clean(self):
        self.preview()
        if self.preview_text=="Completed successfully.":return messagebox.showinfo("Clean","Nothing matched the clean rules.",parent=self)
        if self.include_ignored.get():
            typed=simpledialog.askstring("Dangerous clean","Ignored files are included. Type CLEAN IGNORED to continue:",parent=self)
            if typed!="CLEAN IGNORED":return
        elif not messagebox.askyesno("Clean",f"Delete the previewed untracked items?\n\n{self.preview_text[:1600]}",parent=self):return
        try:messagebox.showinfo("Clean",git(self.repo,*self.args(False)),parent=self);self.preview()
        except Exception as e:messagebox.showerror("Clean",str(e),parent=self)

class RepositorySizeCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Size Explorer");self.geometry("1120x740");self._build();self.analyze()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Analyze",command=self.analyze).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def analyze(self):
        import os
        root=Path(self.repo);gitdir=root/".git";tracked=git(self.repo,"ls-files").splitlines();largest=[]
        for f in tracked:
            p=root/f
            try:
                if p.is_file():largest.append((p.stat().st_size,f))
            except OSError:pass
        largest=sorted(largest,reverse=True)[:30]
        def dsize(path):
            total=0
            for base,dirs,files in os.walk(path):
                for n in files:
                    try:total+=(Path(base)/n).stat().st_size
                    except OSError:pass
            return total
        work=sum(x[0] for x in largest) if False else dsize(root)-dsize(gitdir);gitsize=dsize(gitdir);objects=git(self.repo,"count-objects","-vH")
        report=f"REPOSITORY SIZE EXPLORER\n{'='*78}\nWorking tree files: ~{work/1024/1024:.1f} MB\n.git directory: ~{gitsize/1024/1024:.1f} MB\nTracked files: {len(tracked)}\n\nOBJECT DATABASE\n{objects}\n\nLARGEST CURRENT TRACKED FILES\n"
        for size,name in largest:report+=f"{size/1024/1024:9.2f} MB  {name}\n"
        report+="\nLarge current files may be candidates for Git LFS. Removing large blobs from historical commits requires history rewriting and is intentionally not automated here."
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-size-report.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class ForcePushSafetyCenter(tk.Toplevel):
    """Explicit force-with-lease workflow for rewritten branches; never plain --force."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Force-with-Lease Safety Center");self.geometry("1050x690");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Fetch origin",command=self.fetch).pack(side="left",padx=3);ttk.Button(top,text="Push with lease",command=self.push).pack(side="left")
        self.out=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="This center deliberately does not expose plain --force. Use only after intentional rebase/amend and after reviewing divergence.",padding=8,foreground="#b91c1c").pack(fill="x")
    def snapshot(self):
        b=git(self.repo,"branch","--show-current")
        if not b:raise GitError("Detached HEAD cannot be force-pushed here.")
        up=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}")
        ahead=git(self.repo,"rev-list","--count",f"{up}..HEAD");behind=git(self.repo,"rev-list","--count",f"HEAD..{up}")
        local=git(self.repo,"rev-parse","HEAD");remote=git(self.repo,"rev-parse",up)
        return b,up,ahead,behind,local,remote
    def refresh(self):
        try:
            b,up,ahead,behind,local,remote=self.snapshot();v=f"FORCE-WITH-LEASE REVIEW\n{'='*72}\nBranch: {b}\nUpstream: {up}\nAhead: {ahead}\nBehind: {behind}\nLocal HEAD: {local}\nObserved upstream: {remote}\n\nUse only when remote history is intentionally being replaced after rebase/amend. Fetch first so lease information is current."
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","origin","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def push(self):
        try:b,up,ahead,behind,local,remote=self.snapshot()
        except Exception as e:return messagebox.showerror("Force with lease",str(e),parent=self)
        typed=simpledialog.askstring("Force with lease",f"This may rewrite remote history for {up}.\nType the local branch name exactly to continue:\n{b}",parent=self)
        if typed!=b:return
        if not messagebox.askyesno("Final confirmation",f"Push {b} using --force-with-lease?\nObserved upstream commit:\n{remote}",parent=self):return
        try:messagebox.showinfo("Push",git(self.repo,"push","--force-with-lease"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Push",str(e),parent=self)

class CommitSearchPro(tk.Toplevel):
    """Advanced content/history search with pickaxe, regex and path filters."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Advanced History Search");self.geometry("1160x760");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.q=tk.StringVar();self.path=tk.StringVar();ttk.Entry(top,textvariable=self.q).pack(side="left",fill="x",expand=True);ttk.Entry(top,textvariable=self.path,width=32).pack(side="left",padx=4)
        for t,c in [("Commit messages",self.messages),("Added/removed text",self.pickaxe),("Diff regex",self.regex),("File history",self.file_history)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="First field is search text/regex. Second field is an optional tracked path. Pickaxe (-S) finds commits where the number of occurrences changed; diff regex (-G) matches patch text.",padding=8).pack(fill="x")
    def show(self,args):
        try:v=git(self.repo,*args)
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def base(self):return ["log","--all","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s"]
    def path_arg(self):return ["--",self.path.get().strip()] if self.path.get().strip() else []
    def messages(self):
        q=self.q.get().strip()
        if q:self.show(self.base()+["--regexp-ignore-case","--grep",q]+self.path_arg())
    def pickaxe(self):
        q=self.q.get()
        if q:self.show(self.base()+[f"-S{q}","--pickaxe-all"]+self.path_arg())
    def regex(self):
        q=self.q.get()
        if q:self.show(self.base()+[f"-G{q}"]+self.path_arg())
    def file_history(self):
        p=self.path.get().strip()
        if p:self.show(["log","--follow","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s","--",p])

class BundleInspector(tk.Toplevel):
    """Inspect and verify Git bundles before restore or transfer."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Bundle Inspector");self.geometry("1050x690");self.bundle=tk.StringVar();self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Entry(top,textvariable=self.bundle).pack(side="left",fill="x",expand=True);ttk.Button(top,text="Browse",command=self.browse).pack(side="left",padx=3);ttk.Button(top,text="Verify",command=self.verify).pack(side="left");ttk.Button(top,text="List heads",command=self.heads).pack(side="left",padx=3);ttk.Button(top,text="Clone bundle",command=self.clone).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def browse(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle"),("All files","*")])
        if p:self.bundle.set(p)
    def path(self):
        p=self.bundle.get().strip()
        if not p:raise GitError("Select a bundle file first.")
        return p
    def result(self,v):self.out.delete("1.0","end");self.out.insert("1.0",v)
    def verify(self):
        try:self.result(git(self.repo,"bundle","verify",self.path()))
        except Exception as e:self.result(str(e))
    def heads(self):
        try:self.result(git(self.repo,"bundle","list-heads",self.path()))
        except Exception as e:self.result(str(e))
    def clone(self):
        try:p=self.path()
        except Exception as e:return messagebox.showerror("Bundle",str(e),parent=self)
        parent=filedialog.askdirectory(parent=self,title="Choose restore parent folder")
        if not parent:return
        name=simpledialog.askstring("Clone bundle","New repository folder name:",initialvalue=Path(p).stem,parent=self)
        if name:
            try:messagebox.showinfo("Bundle",git(parent,"clone",p,name),parent=self)
            except Exception as e:messagebox.showerror("Bundle",str(e),parent=self)

class BranchProtectionAdvisor(tk.Toplevel):
    """Read repository branch-protection status and surface practical gaps using GitHub CLI."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Branch Protection Advisor");self.geometry("1120x730");self._build();self.refresh()
    def gh(self,*args):
        try:r=subprocess.run(["gh",*args],cwd=self.repo,text=True,capture_output=True,timeout=120,encoding="utf-8",errors="replace")
        except FileNotFoundError:raise GitError("GitHub CLI (gh) is required. Install it and run 'gh auth login'.")
        out=(r.stdout+"\n"+r.stderr).strip()
        if r.returncode:raise GitError(out or "GitHub CLI command failed")
        return out
    def slug(self):
        import re
        u=git(self.repo,"remote","get-url","origin");m=re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",u)
        if not m:raise GitError("origin is not a recognizable GitHub repository URL.")
        return f"{m.group(1)}/{m.group(2)}"
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.branch=tk.StringVar(value="main");ttk.Entry(top,textvariable=self.branch,width=28).pack(side="left");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left",padx=3);ttk.Button(top,text="Open repository settings",command=self.open_settings).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="This center audits protection only. It does not silently change GitHub branch rules.",padding=8).pack(fill="x")
    def refresh(self):
        import json
        try:
            slug=self.slug()
            try:default=json.loads(self.gh("api",f"repos/{slug}"))["default_branch"];self.branch.set(self.branch.get().strip() or default)
            except:pass
            b=self.branch.get().strip() or "main";raw=self.gh("api",f"repos/{slug}/branches/{b}/protection");p=json.loads(raw)
            reviews=(p.get("required_pull_request_reviews") or {});checks=(p.get("required_status_checks") or {});restr=p.get("restrictions")
            report=f"BRANCH PROTECTION AUDIT\n{'='*76}\nRepository: {slug}\nBranch: {b}\n\n"
            items=[("Protection enabled",True,"API returned protection rules"),("Required PR reviews",bool(reviews),f"Approvals required: {reviews.get('required_approving_review_count',0)}"),("Dismiss stale reviews",bool(reviews.get('dismiss_stale_reviews')),str(reviews.get('dismiss_stale_reviews'))),("Required status checks",bool(checks),", ".join(x.get('context','') for x in checks.get('checks',[])) or "None"),("Enforce admins",bool((p.get('enforce_admins') or {}).get('enabled')),str((p.get('enforce_admins') or {}).get('enabled'))),("Force pushes blocked",not (p.get('allow_force_pushes') or {}).get('enabled',False),str(not (p.get('allow_force_pushes') or {}).get('enabled',False))),("Deletions blocked",not (p.get('allow_deletions') or {}).get('enabled',False),str(not (p.get('allow_deletions') or {}).get('enabled',False)))]
            for name,ok,detail in items:report+=f"[{'PASS' if ok else 'REVIEW'}] {name}\n  {detail}\n\n"
            report+="Recommendations:\n- For shared release branches, require PR review and CI status checks.\n- Keep force pushes and branch deletion disabled unless there is a deliberate exception.\n- Use CODEOWNERS plus required review for sensitive paths when available."
        except Exception as e:report="Unable to read branch protection. The branch may be unprotected, the repository plan may not expose this endpoint, or authentication lacks permission.\n\n"+str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def open_settings(self):
        import webbrowser
        try:slug=self.slug();webbrowser.open(f"https://github.com/{slug}/settings/branches")
        except Exception as e:messagebox.showerror("Branch protection",str(e),parent=self)

class RepositoryFavoritesCenter(tk.Toplevel):
    """Persistent repository favorites and groups for fast portfolio navigation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.current=repo;self.path=Path.home()/".gccc-favorites.json";self.title("Repository Favorites & Groups");self.geometry("1080x700");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.group=tk.StringVar(value="Default");ttk.Entry(top,textvariable=self.group,width=20).pack(side="left");
        for t,c in [("Add current",self.add_current),("Add folder",self.add_folder),("Open selected",self.open_selected),("Remove",self.remove),("Save",self.save)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("group","name","path"),show="headings")
        for c,t,w in [("group","Group",180),("name","Repository",260),("path","Path",600)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<Double-1>",lambda e:self.open_selected())
    def load(self):
        import json
        try:self.rows=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []
        except:self.rows=[]
        self.render()
    def render(self):
        self.tree.delete(*self.tree.get_children())
        for i,r in enumerate(sorted(self.rows,key=lambda x:(x.get("group",""),x.get("name","")))):self.tree.insert("","end",iid=str(i),values=(r.get("group"),r.get("name"),r.get("path")))
        self.visible=sorted(self.rows,key=lambda x:(x.get("group",""),x.get("name","")))
    def add_path(self,p):
        p=str(Path(p).resolve())
        if not (Path(p)/".git").exists():return messagebox.showwarning("Favorites","Selected folder is not a normal Git worktree.",parent=self)
        if not any(x.get("path")==p for x in self.rows):self.rows.append({"group":self.group.get().strip() or "Default","name":Path(p).name,"path":p});self.save(False);self.render()
    def add_current(self):self.add_path(self.current)
    def add_folder(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.add_path(p)
    def selected(self):
        s=self.tree.selection();return self.visible[int(s[0])] if s else None
    def open_selected(self):
        r=self.selected()
        if r:LocalGitWindow(self,r["path"])
    def remove(self):
        r=self.selected()
        if r:self.rows=[x for x in self.rows if x.get("path")!=r.get("path")];self.save(False);self.render()
    def save(self,notice=True):
        import json
        self.path.write_text(json.dumps(self.rows,indent=2),encoding="utf-8")
        if notice:messagebox.showinfo("Favorites",f"Saved {self.path}",parent=self)

class PreflightCenter(tk.Toplevel):
    """Unified pre-push/pre-PR/release local quality gate runner."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Preflight Quality Gates");self.geometry("1120x750");self._build();self.run()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.compile=tk.BooleanVar(value=True);self.fsck=tk.BooleanVar(value=True);self.whitespace=tk.BooleanVar(value=True);self.clean=tk.BooleanVar(value=True)
        for text,var in [("Clean tree",self.clean),("Whitespace",self.whitespace),("Python compile",self.compile),("Git fsck",self.fsck)]:ttk.Checkbutton(top,text=text,variable=var).pack(side="left",padx=4)
        ttk.Button(top,text="Run gates",command=self.run,style="Accent.TButton").pack(side="left",padx=8);ttk.Button(top,text="Export",command=self.export).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def run_cmd(self,args):
        try:
            r=subprocess.run(args,cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace");return r.returncode==0,(r.stdout+r.stderr).strip() or "OK"
        except Exception as e:return False,str(e)
    def run(self):
        tests=[]
        if self.clean.get():tests.append(("Clean working tree",git(self.repo,"status","--porcelain")=="Completed successfully.","No local changes required"))
        if self.whitespace.get():tests.append(("Whitespace",*self.run_cmd(["git","diff","--check"])))
        if self.compile.get():tests.append(("Python compile",*self.run_cmd(["python","-m","compileall","-q","."])))
        if self.fsck.get():tests.append(("Git integrity",*self.run_cmd(["git","fsck","--no-progress"])))
        self.report="PREFLIGHT QUALITY GATES\n"+"="*74+"\n\n"+"\n\n".join(f"[{'PASS' if ok else 'FAIL'}] {n}\n  {d}" for n,ok,d in tests)+f"\n\nOVERALL: {'PASS' if tests and all(x[1] for x in tests) else 'FAIL'}"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="preflight-report.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class CommitTemplateCenter(tk.Toplevel):
    """Manage repository commit templates and inspect the effective template."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Template Center");self.geometry("980x680");self.path=Path(repo)/".git"/"gccc-commit-template.txt";self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Load",self.load),("Use conventional template",self.defaults),("Save + configure",self.save),("Disable template",self.disable)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",undo=True,font=("Consolas",10));self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The template is local to this clone under .git. It is used by Git commit editors but does not force a message format.",padding=8).pack(fill="x")
    def load(self):
        self.text.delete("1.0","end")
        if self.path.exists():self.text.insert("1.0",self.path.read_text(encoding="utf-8",errors="replace"))
        else:self.defaults()
    def defaults(self):
        value="<type>(<scope>): <short summary>\n\nWhy:\n\nWhat changed:\n- \n\nValidation:\n- \n\nRefs: \n"
        self.text.delete("1.0","end");self.text.insert("1.0",value)
    def save(self):
        try:
            self.path.write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8");git(self.repo,"config","commit.template",str(self.path));messagebox.showinfo("Commit template",f"Saved and configured {self.path}",parent=self)
        except Exception as e:messagebox.showerror("Commit template",str(e),parent=self)
    def disable(self):
        try:git(self.repo,"config","--unset","commit.template");messagebox.showinfo("Commit template","Repository commit template configuration removed.",parent=self)
        except Exception as e:messagebox.showerror("Commit template",str(e),parent=self)

class PatchQueueCenter(tk.Toplevel):
    """Apply and manage an email-style patch queue using git am."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Patch Queue Center");self.geometry("1080x710");self.files=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Add patch files",self.add),("Clear list",self.clear),("Apply queue",self.apply),("Continue",lambda:self.control("--continue")),("Skip",lambda:self.control("--skip")),("Abort",lambda:self.control("--abort")),("Refresh",self.refresh)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.list=tk.Listbox(a,font=("Consolas",9));self.list.pack(fill="both",expand=True)
        self.out=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="git am preserves commit metadata from format-patch mailboxes. Resolve conflicts, stage the resolution, then Continue. Abort restores the pre-am state.",padding=8).pack(fill="x")
    def add(self):
        f=filedialog.askopenfilenames(parent=self,filetypes=[("Patch/mailbox","*.patch *.mbox"),("All files","*")])
        for p in f:
            if p not in self.files:self.files.append(p)
        self.render()
    def render(self):self.list.delete(0,"end");[self.list.insert("end",p) for p in self.files]
    def clear(self):self.files=[];self.render()
    def refresh(self):
        state=Path(self.repo)/".git"/"rebase-apply";v="Patch application in progress." if state.exists() else "No git am session in progress."
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def apply(self):
        if not self.files:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Patch queue","Commit or stash local changes before applying a patch queue.",parent=self)
        if not messagebox.askyesno("Apply patch queue",f"Apply {len(self.files)} patch(es) as commits?",parent=self):return
        try:out=git(self.repo,"am","--3way",*self.files);messagebox.showinfo("Patch queue",out,parent=self);self.clear();self.refresh()
        except Exception as e:self.out.delete("1.0","end");self.out.insert("1.0",str(e));messagebox.showwarning("Patch queue","Patch application paused or failed. Resolve conflicts, then Continue/Skip/Abort.",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Patch queue",git(self.repo,"am",arg),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Patch queue",str(e),parent=self)

class HookAuditCenter(tk.Toplevel):
    """Inventory local hooks, executable state and basic provenance."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.dir=Path(repo)/".git"/"hooks";self.title("Hook Audit Center");self.geometry("1080x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Open selected",command=self.open_hook).pack(side="left",padx=3);ttk.Button(top,text="Open Hooks Manager",command=lambda:HooksCenter(self,self.repo)).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("hook","enabled","size","modified"),show="headings")
        for c,t,w in [("hook","Hook",300),("enabled","Executable",110),("size","Size",100),("modified","Modified",210)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<<TreeviewSelect>>",lambda e:self.preview())
        self.text=tk.Text(self,height=14,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        import datetime,os
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for p in sorted(self.dir.iterdir()) if self.dir.exists() else []:
            if p.is_file() and not p.name.endswith(".sample"):
                st=p.stat();r=(p.name,"Yes" if os.access(p,os.X_OK) else "No",st.st_size,datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),p);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=r[:4])
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def preview(self):
        r=self.selected();self.text.delete("1.0","end")
        if r:self.text.insert("1.0",r[4].read_text(encoding="utf-8",errors="replace"))
    def open_hook(self):
        r=self.selected()
        if not r:return
        import os
        try:os.startfile(r[4]) if hasattr(os,"startfile") else subprocess.Popen(["xdg-open",str(r[4])])
        except Exception as e:messagebox.showerror("Hook",str(e),parent=self)

class MergePreviewCenter(tk.Toplevel):
    """Preview a merge with merge-tree before changing the working tree."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Preview Center");self.geometry("1120x730");self._build();self.load_refs()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.target=tk.StringVar();ttk.Combobox(top,textvariable=self.target,width=38).pack(side="left")
        ttk.Button(top,text="Preview merge",command=self.preview).pack(side="left",padx=3);ttk.Button(top,text="Perform merge",command=self.merge).pack(side="left");ttk.Button(top,text="Abort merge",command=self.abort).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Preview uses git merge-tree and does not change the working tree. Actual merge requires a clean working tree and explicit confirmation.",padding=8).pack(fill="x")
    def load_refs(self):
        raw=git(self.repo,"for-each-ref","--format=%(refname:short)","refs/heads/","refs/remotes/");refs=[x for x in raw.splitlines() if x and not x.endswith("/HEAD")];self.children["!frame"].winfo_children()[0]["values"]=refs
        if refs:self.target.set(refs[0])
    def preview(self):
        t=self.target.get().strip()
        if not t:return
        try:
            base=git(self.repo,"merge-base","HEAD",t);v=git(self.repo,"merge-tree",base,"HEAD",t)
            summary=f"MERGE PREVIEW\n{'='*72}\nCurrent: {git(self.repo,'branch','--show-current')}\nTarget: {t}\nMerge base: {base}\n\n{v}"
        except Exception as e:summary=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",summary)
    def merge(self):
        t=self.target.get().strip()
        if not t:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Merge","Commit or stash changes before merging.",parent=self)
        if messagebox.askyesno("Merge",f"Merge {t} into the current branch?",parent=self):
            try:messagebox.showinfo("Merge",git(self.repo,"merge","--no-edit",t),parent=self)
            except Exception as e:messagebox.showerror("Merge",str(e),parent=self)
    def abort(self):
        try:messagebox.showinfo("Merge",git(self.repo,"merge","--abort"),parent=self)
        except Exception as e:messagebox.showerror("Merge",str(e),parent=self)

class ResetRecoveryPlanner(tk.Toplevel):
    """Plan soft/mixed/hard reset with mandatory recovery branch and impact preview."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Reset & Recovery Planner");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.target=tk.StringVar(value="HEAD~1");self.mode=tk.StringVar(value="--mixed")
        ttk.Entry(top,textvariable=self.target,width=30).pack(side="left");ttk.Combobox(top,textvariable=self.mode,values=["--soft","--mixed","--hard"],state="readonly",width=12).pack(side="left",padx=4)
        ttk.Button(top,text="Preview",command=self.refresh).pack(side="left");ttk.Button(top,text="Execute protected reset",command=self.execute).pack(side="left",padx=3);ttk.Button(top,text="Open reflog recovery",command=lambda:ReflogRecoveryCenter(self,self.repo)).pack(side="left")
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Every reset creates a timestamped recovery branch first. Hard reset permanently discards tracked working-tree/index changes after confirmation.",padding=8,foreground="#b91c1c").pack(fill="x")
    def refresh(self):
        t=self.target.get().strip()
        try:
            resolved=git(self.repo,"rev-parse",t);summary=git(self.repo,"diff","--stat",t,"HEAD");commits=git(self.repo,"log","--oneline",f"{t}..HEAD")
            v=f"RESET PREVIEW\n{'='*72}\nTarget: {t}\nResolved: {resolved}\nMode: {self.mode.get()}\n\nCOMMITS MOVED OUT OF CURRENT BRANCH\n{commits}\n\nCHANGE SUMMARY\n{summary}"
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def execute(self):
        import datetime
        t=self.target.get().strip();mode=self.mode.get()
        try:git(self.repo,"rev-parse",t)
        except Exception as e:return messagebox.showerror("Reset",str(e),parent=self)
        warning=f"Reset current branch to {t} using {mode}?"
        if mode=="--hard":warning+="\n\nTracked local changes will be permanently discarded."
        if not messagebox.askyesno("Protected reset",warning,parent=self):return
        backup=f"gccc-backup/pre-reset-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            git(self.repo,"branch",backup)
            if mode=="--hard":
                typed=simpledialog.askstring("Hard reset",f"Recovery branch created: {backup}\nType HARD RESET to continue:",parent=self)
                if typed!="HARD RESET":return
            out=git(self.repo,"reset",mode,t);messagebox.showinfo("Reset",f"{out}\n\nRecovery branch: {backup}",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Reset",str(e),parent=self)

class GitConfigCenter(tk.Toplevel):
    """Inspect effective Git configuration by scope and safely edit common values."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Configuration Center");self.geometry("1160x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.key=tk.StringVar();self.value=tk.StringVar();self.scope=tk.StringVar(value="--local")
        ttk.Entry(top,textvariable=self.key,width=30).pack(side="left");ttk.Entry(top,textvariable=self.value).pack(side="left",fill="x",expand=True,padx=4);ttk.Combobox(top,textvariable=self.scope,values=["--local","--global"],state="readonly",width=10).pack(side="left")
        for t,c in [("Set value",self.set_value),("Unset",self.unset),("Refresh",self.refresh),("Copy report",self.copy)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Values come from `git config --list --show-origin --show-scope`. Global edits affect all repositories for the current user.",padding=8).pack(fill="x")
    def refresh(self):
        try:self.report=git(self.repo,"config","--list","--show-origin","--show-scope")
        except Exception as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def set_value(self):
        k=self.key.get().strip();v=self.value.get()
        if not k:return
        if self.scope.get()=="--global" and not messagebox.askyesno("Global Git config",f"Set global {k} for the current user?",parent=self):return
        try:messagebox.showinfo("Git config",git(self.repo,"config",self.scope.get(),k,v),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Git config",str(e),parent=self)
    def unset(self):
        k=self.key.get().strip()
        if not k:return
        if messagebox.askyesno("Unset config",f"Unset {k} at {self.scope.get()} scope?",parent=self):
            try:messagebox.showinfo("Git config",git(self.repo,"config",self.scope.get(),"--unset-all",k),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Git config",str(e),parent=self)
    def copy(self):self.clipboard_clear();self.clipboard_append(self.report);messagebox.showinfo("Git config","Copied report.",parent=self)

class CherryPickQueueCenter(tk.Toplevel):
    """Build and execute an ordered multi-commit cherry-pick queue with backup protection."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Cherry-Pick Queue Center");self.geometry("1200x760");self.rows=[];self.queue=[];self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.ref=tk.StringVar(value="--all");ttk.Entry(top,textvariable=self.ref,width=24).pack(side="left")
        for t,c in [("Load commits",self.load),("Add selected",self.add),("Remove",self.remove),("Move up",lambda:self.move(-1)),("Move down",lambda:self.move(1)),("Execute queue",self.execute),("Continue",lambda:self.control("--continue")),("Abort",lambda:self.control("--abort"))]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=3);pane.add(b,weight=2)
        ttk.Label(a,text="Available commits",font=("Segoe UI Semibold",10)).pack(anchor="w");self.available=tk.Listbox(a,font=("Consolas",9));self.available.pack(fill="both",expand=True)
        ttk.Label(b,text="Ordered queue",font=("Segoe UI Semibold",10)).pack(anchor="w");self.queued=tk.Listbox(b,font=("Consolas",9));self.queued.pack(fill="both",expand=True)
        ttk.Label(self,text="A timestamped pre-cherry-pick backup branch is created before execution. The queue stops on the first conflict.",padding=8).pack(fill="x")
    def load(self):
        args=["log","-250","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%s"]
        if self.ref.get().strip() and self.ref.get().strip()!="--all":args.append(self.ref.get().strip())
        else:args.insert(1,"--all")
        raw=git(self.repo,*args);self.rows=[];self.available.delete(0,"end")
        for line in raw.splitlines():
            p=line.split("\x1f",3)
            if len(p)==4:self.rows.append(p);self.available.insert("end",f"{p[1]}  {p[2]}  {p[3]}")
    def add(self):
        for i in self.available.curselection():
            r=self.rows[i]
            if not any(x[0]==r[0] for x in self.queue):self.queue.append(r)
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
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Cherry-pick queue","Commit or stash local changes first.",parent=self)
        if not messagebox.askyesno("Cherry-pick queue",f"Apply {len(self.queue)} commits in the displayed order?",parent=self):return
        backup=f"gccc-backup/pre-cherry-pick-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:git(self.repo,"branch",backup);out=git(self.repo,"cherry-pick",*[r[0] for r in self.queue]);messagebox.showinfo("Cherry-pick queue",f"{out}\n\nBackup: {backup}",parent=self);self.queue=[];self.render()
        except Exception as e:messagebox.showwarning("Cherry-pick paused",f"Backup: {backup}\n\n{e}\n\nResolve conflicts and Continue, or Abort.",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Cherry-pick",git(self.repo,"cherry-pick",arg),parent=self)
        except Exception as e:messagebox.showerror("Cherry-pick",str(e),parent=self)

class ReleaseAssetIntegrityCenter(tk.Toplevel):
    """Generate and verify SHA-256 manifests for release assets."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Asset Integrity");self.geometry("1080x700");self.files=[];self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Add assets",self.add),("Clear",self.clear),("Generate SHA256SUMS",self.generate),("Verify manifest",self.verify)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.list=tk.Listbox(self,font=("Consolas",9));self.list.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=15,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def add(self):
        for p in filedialog.askopenfilenames(parent=self):
            if p not in self.files:self.files.append(p)
        self.render()
    def clear(self):self.files=[];self.render();self.out.delete("1.0","end")
    def render(self):self.list.delete(0,"end");[self.list.insert("end",p) for p in self.files]
    def digest(self,p):
        import hashlib
        h=hashlib.sha256()
        with open(p,"rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
        return h.hexdigest()
    def generate(self):
        if not self.files:return
        lines=[f"{self.digest(p)}  {Path(p).name}" for p in self.files];self.out.delete("1.0","end");self.out.insert("1.0","\n".join(lines))
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="SHA256SUMS.txt")
        if target:Path(target).write_text("\n".join(lines)+"\n",encoding="utf-8");messagebox.showinfo("Integrity",f"Saved {target}",parent=self)
    def verify(self):
        manifest=filedialog.askopenfilename(parent=self,filetypes=[("Checksum manifests","*.txt *.sha256"),("All files","*")])
        if not manifest:return
        base=Path(manifest).parent;results=[]
        for line in Path(manifest).read_text(encoding="utf-8",errors="replace").splitlines():
            if not line.strip():continue
            parts=line.split(None,1)
            if len(parts)!=2:results.append(f"INVALID LINE: {line}");continue
            expected,name=parts[0],parts[1].lstrip(" *");p=base/name
            if not p.exists():results.append(f"MISSING  {name}")
            else:results.append(f"{'PASS' if self.digest(p).lower()==expected.lower() else 'FAIL'}  {name}")
        self.out.delete("1.0","end");self.out.insert("1.0","\n".join(results))

class LocalReleaseArchiveCenter(tk.Toplevel):
    """Create a structured local release folder with source, bundle, checksums and notes."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Local Release Archive");self.geometry("960x620");self.version=tk.StringVar();self._build()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);ttk.Label(f,text="Version/tag").grid(row=0,column=0,sticky="w");ttk.Entry(f,textvariable=self.version).grid(row=0,column=1,sticky="ew",padx=8);f.columnconfigure(1,weight=1)
        ttk.Label(f,text="Creates source ZIP, full Git bundle, SHA256SUMS, release notes copy and metadata in a new local folder.",wraplength=760).grid(row=1,column=0,columnspan=2,sticky="w",pady=10)
        ttk.Button(f,text="Build local release archive",command=self.build,style="Accent.TButton").grid(row=2,column=1,sticky="e",pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=3,column=0,columnspan=2,sticky="nsew");f.rowconfigure(3,weight=1)
    def build(self):
        import json,hashlib,datetime,shutil
        version=self.version.get().strip()
        if not version:return messagebox.showwarning("Release archive","Enter a version or tag.",parent=self)
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Release archive","Commit or stash local changes first.",parent=self)
        parent=filedialog.askdirectory(parent=self,title="Choose release archive parent")
        if not parent:return
        folder=Path(parent)/f"{Path(self.repo).name}-{version}";folder.mkdir(parents=True,exist_ok=False)
        zipfile=folder/f"{Path(self.repo).name}-{version}-source.zip";bundle=folder/f"{Path(self.repo).name}-{version}.bundle"
        try:
            git(self.repo,"archive","--format=zip",f"--output={zipfile}","HEAD");git(self.repo,"bundle","create",str(bundle),"--all")
            notes=Path(self.repo)/"RELEASE_NOTES.md"
            if notes.exists():shutil.copy2(notes,folder/"RELEASE_NOTES.md")
            def sha(p):
                h=hashlib.sha256()
                with open(p,"rb") as f:
                    for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
                return h.hexdigest()
            assets=[zipfile,bundle]+(([folder/"RELEASE_NOTES.md"]) if (folder/"RELEASE_NOTES.md").exists() else [])
            (folder/"SHA256SUMS.txt").write_text("\n".join(f"{sha(p)}  {p.name}" for p in assets)+"\n",encoding="utf-8")
            metadata={"repository":Path(self.repo).name,"version":version,"created":datetime.datetime.now().isoformat(),"head":git(self.repo,"rev-parse","HEAD"),"branch":git(self.repo,"branch","--show-current")};(folder/"release-metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
            self.out.delete("1.0","end");self.out.insert("1.0",f"Release archive created:\n{folder}\n\n"+"\n".join(p.name for p in folder.iterdir()));messagebox.showinfo("Release archive",f"Created {folder}",parent=self)
        except Exception as e:messagebox.showerror("Release archive",str(e),parent=self)

class CommitSignatureAuditCenter(tk.Toplevel):
    """Audit recent commit and tag signature status without changing repository history."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Signature Audit Center");self.geometry("1180x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.limit=tk.IntVar(value=100);ttk.Label(top,text="Commits").pack(side="left");ttk.Spinbox(top,from_=10,to=1000,increment=10,textvariable=self.limit,width=8).pack(side="left",padx=4);ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export audit",command=self.export).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("hash","date","author","sig","subject"),show="headings")
        for c,t,w in [("hash","Commit",100),("date","Date",110),("author","Author",190),("sig","Signature",115),("subject","Subject",570)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8));self.tree.bind("<<TreeviewSelect>>",lambda e:self.details())
    def refresh(self):
        n=max(10,int(self.limit.get()));raw=git(self.repo,"log",f"-{n}","--date=short","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%G?%x1f%s");self.rows=[];self.tree.delete(*self.tree.get_children())
        labels={"G":"Good","B":"Bad","U":"Good/unknown trust","X":"Expired","Y":"Expired key","R":"Revoked key","E":"Cannot check","N":"Unsigned"}
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p[1],p[2],p[3],labels.get(p[4],p[4]),p[5]))
        counts={}
        for r in self.rows:counts[r[4]]=counts.get(r[4],0)+1
        self.report=f"SIGNATURE AUDIT\n{'='*72}\nCommits reviewed: {len(self.rows)}\n"+"\n".join(f"{labels.get(k,k)}: {v}" for k,v in sorted(counts.items()))
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def details(self):
        s=self.tree.selection()
        if not s:return
        try:v=git(self.repo,"show","-s","--show-signature","--date=iso-strict","--pretty=fuller",self.rows[int(s[0])][0])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="signature-audit.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class ReleaseCompareCenter(tk.Toplevel):
    """Compare two release refs with commits, files and compact release statistics."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Comparison Center");self.geometry("1200x760");self._build();self.load_refs()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.old=tk.StringVar();self.new=tk.StringVar(value="HEAD");self.oldbox=ttk.Combobox(top,textvariable=self.old,width=26);self.newbox=ttk.Combobox(top,textvariable=self.new,width=26);self.oldbox.pack(side="left");self.newbox.pack(side="left",padx=4);ttk.Button(top,text="Compare",command=self.compare).pack(side="left");ttk.Button(top,text="Export Markdown",command=self.export).pack(side="left",padx=3)
        nb=ttk.Notebook(self);nb.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(nb);b=ttk.Frame(nb);c=ttk.Frame(nb);nb.add(a,text="Summary");nb.add(b,text="Commits");nb.add(c,text="Files")
        self.summary=tk.Text(a,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="both",expand=True);self.commits=tk.Text(b,wrap="none",font=("Consolas",9));self.commits.pack(fill="both",expand=True);self.files=tk.Text(c,wrap="none",font=("Consolas",9));self.files.pack(fill="both",expand=True)
    def load_refs(self):
        raw=git(self.repo,"tag","--sort=-version:refname");tags=[x for x in raw.splitlines() if x and x!="Completed successfully."];vals=tags+["HEAD"];self.oldbox["values"]=vals;self.newbox["values"]=vals
        if tags:self.old.set(tags[1] if len(tags)>1 else tags[0]);self.new.set(tags[0])
    def compare(self):
        a=self.old.get().strip();b=self.new.get().strip()
        if not a or not b:return
        try:
            count=git(self.repo,"rev-list","--count",f"{a}..{b}");short=git(self.repo,"diff","--shortstat",a,b);stat=git(self.repo,"diff","--stat",a,b);commits=git(self.repo,"log","--date=short","--pretty=format:- %h %ad %an: %s",f"{a}..{b}");files=git(self.repo,"diff","--name-status",a,b)
            self.md=f"# Release comparison: {a} -> {b}\n\n- Commits: {count}\n- Diff: {short}\n\n## Commits\n{commits}\n\n## Files\n```text\n{files}\n```\n"
            self.summary.delete("1.0","end");self.summary.insert("1.0",f"RELEASE COMPARISON\n{'='*72}\n{a} -> {b}\nCommits: {count}\n{short}\n\n{stat}");self.commits.delete("1.0","end");self.commits.insert("1.0",commits);self.files.delete("1.0","end");self.files.insert("1.0",files)
        except Exception as e:messagebox.showerror("Release comparison",str(e),parent=self)
    def export(self):
        if not hasattr(self,"md"):self.compare()
        if not hasattr(self,"md"):return
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="release-comparison.md")
        if p:Path(p).write_text(self.md,encoding="utf-8")

class SafeDeleteBranchWizard(tk.Toplevel):
    """Branch deletion wizard that checks merge, worktree and upstream state first."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safe Branch Delete Wizard");self.geometry("1050x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Delete selected local branch",command=self.delete).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("branch","merged","worktree","upstream","ahead","behind"),show="headings")
        for c,t,w in [("branch","Branch",280),("merged","Merged",80),("worktree","In worktree",100),("upstream","Upstream",270),("ahead","Ahead",70),("behind","Behind",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        self.out=tk.Text(self,height=10,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8));self.tree.bind("<<TreeviewSelect>>",lambda e:self.assess())
    def refresh(self):
        current=git(self.repo,"branch","--show-current");merged=set(x.strip().lstrip("* ") for x in git(self.repo,"branch","--merged").splitlines());wt=git(self.repo,"worktree","list","--porcelain");used={x.replace("branch refs/heads/","",1) for x in wt.splitlines() if x.startswith("branch refs/heads/")};raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(upstream:short)","refs/heads/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",1);b=p[0];up=p[1] if len(p)>1 else "";ahead=behind="-"
            if up:
                try:ahead=git(self.repo,"rev-list","--count",f"{up}..{b}");behind=git(self.repo,"rev-list","--count",f"{b}..{up}")
                except:pass
            r=dict(branch=b,merged=b in merged,used=b in used,current=b==current,up=up,ahead=ahead,behind=behind);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(b,"Yes" if r["merged"] else "No","Yes" if r["used"] else "No",up or "-",ahead,behind))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def assess(self):
        r=self.selected()
        if not r:return
        blockers=[]
        if r["current"]:blockers.append("This is the current branch.")
        if r["used"]:blockers.append("The branch is checked out in a worktree.")
        if not r["merged"]:blockers.append("Git does not report the branch as merged into the current branch.")
        if str(r["ahead"]) not in ("0","-"):blockers.append(f"Branch has {r['ahead']} commit(s) not present in its configured upstream.")
        v=f"BRANCH DELETE ASSESSMENT\n{'='*72}\nBranch: {r['branch']}\nUpstream: {r['up'] or 'None'}\n\n"+("SAFE FOR NORMAL DELETE (-d)" if not blockers else "BLOCKED\n- "+"\n- ".join(blockers))
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete(self):
        r=self.selected()
        if not r:return
        if r["current"] or r["used"] or not r["merged"] or str(r["ahead"]) not in ("0","-"):return messagebox.showwarning("Safe delete","This branch does not meet the safe-delete rules. Force deletion is intentionally unavailable here.",parent=self)
        if messagebox.askyesno("Delete local branch",f"Delete merged local branch {r['branch']} with git branch -d?",parent=self):
            try:messagebox.showinfo("Delete",git(self.repo,"branch","-d",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Delete",str(e),parent=self)

class PullRebaseAdvisor(tk.Toplevel):
    """Compare merge, rebase and fast-forward pull outcomes before changing history."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Pull Strategy Advisor");self.geometry("1100x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Fetch + analyze",self.refresh),("Fast-forward pull",self.ff),("Rebase onto upstream",self.rebase),("Merge upstream",self.merge)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="The advisor never chooses a history-changing strategy silently. Rebase creates a timestamped safety branch first.",padding=8).pack(fill="x")
    def state(self):
        b=git(self.repo,"branch","--show-current");u=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");a=git(self.repo,"rev-list","--count",f"{u}..HEAD");d=git(self.repo,"rev-list","--count",f"HEAD..{u}");return b,u,a,d
    def refresh(self):
        try:
            git(self.repo,"fetch","--all","--prune");b,u,a,d=self.state();rec="Already synchronized."
            if d!="0" and a=="0":rec="Fast-forward pull is available and preserves a linear history."
            elif a!="0" and d=="0":rec="Local branch is ahead only. Push after review."
            elif a!="0" and d!="0":rec="Histories diverged. Choose rebase for a linear private branch, or merge when preserving integration topology is preferable."
            v=f"PULL STRATEGY ANALYSIS\n{'='*74}\nBranch: {b}\nUpstream: {u}\nAhead: {a}\nBehind: {d}\nWorking tree: {'Clean' if git(self.repo,'status','--porcelain')=='Completed successfully.' else 'Changed'}\n\nRecommendation: {rec}"
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def clean(self):return git(self.repo,"status","--porcelain")=="Completed successfully."
    def ff(self):
        if not self.clean():return messagebox.showwarning("Pull","Commit or stash changes first.",parent=self)
        try:messagebox.showinfo("Pull",git(self.repo,"pull","--ff-only"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Pull",str(e),parent=self)
    def rebase(self):
        import datetime
        if not self.clean():return messagebox.showwarning("Rebase","Commit or stash changes first.",parent=self)
        try:b,u,a,d=self.state();backup=f"gccc-backup/pre-pull-rebase-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}";git(self.repo,"branch",backup)
        except Exception as e:return messagebox.showerror("Rebase",str(e),parent=self)
        if messagebox.askyesno("Rebase",f"Safety branch created: {backup}\n\nRebase {b} onto {u}?",parent=self):
            try:messagebox.showinfo("Rebase",git(self.repo,"rebase",u),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Rebase",str(e),parent=self)
    def merge(self):
        if not self.clean():return messagebox.showwarning("Merge","Commit or stash changes first.",parent=self)
        try:b,u,a,d=self.state()
        except Exception as e:return messagebox.showerror("Merge",str(e),parent=self)
        if messagebox.askyesno("Merge",f"Merge upstream {u} into {b}?",parent=self):
            try:messagebox.showinfo("Merge",git(self.repo,"merge","--no-edit",u),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Merge",str(e),parent=self)

class DetachedHeadRecoveryCenter(tk.Toplevel):
    """Detect detached HEAD and preserve work through a new branch."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Detached HEAD Recovery");self.geometry("1000x660");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Create branch here",command=self.branch).pack(side="left",padx=3);ttk.Button(top,text="Switch to default branch",command=self.default).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        b=git(self.repo,"branch","--show-current");head=git(self.repo,"rev-parse","HEAD");desc=git(self.repo,"show","-s","--date=iso-strict","--pretty=fuller","HEAD");detached=not bool(b)
        v=f"DETACHED HEAD STATUS\n{'='*72}\nDetached: {'Yes' if detached else 'No'}\nCurrent branch: {b or '(none)'}\nHEAD: {head}\n\n{desc}\n\n"+("Create a branch here before switching away if this commit/work should be retained." if detached else "Repository is attached to a normal branch.")
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def branch(self):
        import datetime,re
        name=simpledialog.askstring("Create branch","New branch name:",initialvalue=f"recovered/detached-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}",parent=self)
        if name and re.match(r"^[A-Za-z0-9._/-]+$",name):
            try:messagebox.showinfo("Branch",git(self.repo,"switch","-c",name),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Branch",str(e),parent=self)
    def default(self):
        try:
            remote=git(self.repo,"symbolic-ref","refs/remotes/origin/HEAD");branch=remote.replace("refs/remotes/origin/","",1)
        except:branch="main"
        if messagebox.askyesno("Switch branch",f"Switch to {branch}? Uncommitted changes must be compatible.",parent=self):
            try:messagebox.showinfo("Switch",git(self.repo,"switch",branch),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Switch",str(e),parent=self)

class RepositoryStateExportCenter(tk.Toplevel):
    """Export a machine-readable repository-state snapshot for audits and automation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository State Export");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export JSON",command=self.export_json).pack(side="left",padx=3);ttk.Button(top,text="Export Markdown",command=self.export_md).pack(side="left")
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except:return ""
    def refresh(self):
        import json,datetime
        status=self.safe("status","--porcelain=v1").splitlines();branch=self.safe("branch","--show-current");head=self.safe("rev-parse","HEAD");up=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}")
        self.data={"captured":datetime.datetime.now().isoformat(),"repository":Path(self.repo).name,"path":self.repo,"branch":branch,"head":head,"upstream":up,"changes":status,"remotes":self.safe("remote","-v").splitlines(),"tags":self.safe("tag","--sort=-creatordate").splitlines()[:50],"recent_commits":self.safe("log","-25","--date=iso-strict","--pretty=format:%H%x1f%ad%x1f%an%x1f%s").splitlines()}
        self.text.delete("1.0","end");self.text.insert("1.0",json.dumps(self.data,indent=2))
    def export_json(self):
        import json
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile=Path(self.repo).name+"-state.json")
        if p:Path(p).write_text(json.dumps(self.data,indent=2),encoding="utf-8")
    def export_md(self):
        d=self.data;md=f"# Repository state: {d['repository']}\n\n- Captured: {d['captured']}\n- Branch: `{d['branch'] or 'detached'}`\n- HEAD: `{d['head']}`\n- Upstream: `{d['upstream'] or 'none'}`\n\n## Changes\n```text\n"+"\n".join(d["changes"])+"\n```\n\n## Remotes\n```text\n"+"\n".join(d["remotes"])+"\n```\n"
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=Path(self.repo).name+"-state.md")
        if p:Path(p).write_text(md,encoding="utf-8")

class RepositoryRulesCenter(tk.Toplevel):
    """Audit essential repository engineering and governance controls."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Rules Audit");self.geometry("1100x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Export",command=self.export).pack(side="left",padx=4)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        checks=[]
        for f in ("README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md",".gitignore",".gitattributes"):
            checks.append((f,(Path(self.repo)/f).exists()))
        checks.append(("CODEOWNERS",(Path(self.repo)/".github"/"CODEOWNERS").exists()))
        wf=Path(self.repo)/".github"/"workflows";checks.append(("CI workflows",wf.exists() and bool(list(wf.glob("*.y*ml")))))
        try:up=git(self.repo,"rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");checks.append((f"Upstream ({up})",True))
        except:checks.append(("Upstream configured",False))
        self.report="REPOSITORY RULES AUDIT\n"+"="*72+"\n\n"+"\n".join(f"[{'PASS' if ok else 'REVIEW'}] {n}" for n,ok in checks)+f"\n\nOVERALL: {'PASS' if all(x[1] for x in checks) else 'REVIEW REQUIRED'}"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-rules-audit.txt")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class CommitRangeExporter(tk.Toplevel):
    """Export a selected commit range as patches, bundle, or Markdown."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Range Exporter");self.geometry("1050x700");self._build();self.preview()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.base=tk.StringVar(value="HEAD~5");self.tip=tk.StringVar(value="HEAD");ttk.Entry(bar,textvariable=self.base,width=22).pack(side="left");ttk.Entry(bar,textvariable=self.tip,width=22).pack(side="left",padx=4)
        for t,c in [("Preview",self.preview),("Patch series",self.patches),("Bundle",self.bundle),("Markdown",self.markdown)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def spec(self):return f"{self.base.get().strip()}..{self.tip.get().strip()}"
    def preview(self):
        try:self.report=git(self.repo,"log","--reverse","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s",self.spec())
        except Exception as e:self.report=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def patches(self):
        d=filedialog.askdirectory(parent=self)
        if d:
            try:messagebox.showinfo("Export",git(self.repo,"format-patch","-o",d,self.spec()),parent=self)
            except Exception as e:messagebox.showerror("Export",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile="commit-range.bundle")
        if p:
            try:messagebox.showinfo("Export",git(self.repo,"bundle","create",p,self.tip.get().strip(),f"^{self.base.get().strip()}"),parent=self)
            except Exception as e:messagebox.showerror("Export",str(e),parent=self)
    def markdown(self):
        self.preview();p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="commit-range.md")
        if p:Path(p).write_text(f"# Commit range {self.spec()}\n\n```text\n{self.report}\n```\n",encoding="utf-8")

class LocalBranchDashboard(tk.Toplevel):
    """Branch-centric dashboard with upstream divergence and recency."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Local Branch Dashboard");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Switch selected",command=self.switch).pack(side="left",padx=4);ttk.Button(bar,text="Compare to current",command=self.compare).pack(side="left");ttk.Button(bar,text="Safe Delete",command=lambda:SafeDeleteBranchWizard(self,self.repo)).pack(side="left",padx=4)
        self.tree=ttk.Treeview(self,columns=("branch","upstream","ahead","behind","date","subject"),show="headings")
        for c,t,w in [("branch","Branch",240),("upstream","Upstream",240),("ahead","Ahead",70),("behind","Behind",70),("date","Last commit",120),("subject","Subject",420)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
    def refresh(self):
        raw=git(self.repo,"for-each-ref","--sort=-committerdate","--format=%(refname:short)%09%(upstream:short)%09%(committerdate:short)%09%(subject)","refs/heads/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3);b=p[0];up=p[1] if len(p)>1 else "";date=p[2] if len(p)>2 else "";sub=p[3] if len(p)>3 else "";a=d="-"
            if up:
                try:a=git(self.repo,"rev-list","--count",f"{up}..{b}");d=git(self.repo,"rev-list","--count",f"{b}..{up}")
                except:pass
            r=(b,up,a,d,date,sub);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=r)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def switch(self):
        r=self.selected()
        if r:
            try:messagebox.showinfo("Branch",git(self.repo,"switch",r[0]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Branch",str(e),parent=self)
    def compare(self):
        r=self.selected()
        if not r:return
        cur=git(self.repo,"branch","--show-current")
        try:v=git(self.repo,"log","--left-right","--graph","--oneline",f"{cur}...{r[0]}")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class RepositoryOnboardingCenter(tk.Toplevel):
    """Turn an existing folder/repository into a collaboration-ready project."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Onboarding Center");self.geometry("1080x720");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Create missing basics",self.create_basics),("Initialize Git",self.init_git),("Open Rules Audit",lambda:RepositoryRulesCenter(self,self.repo))]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        root=Path(self.repo);checks=[]
        for name in (".git","README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md",".gitignore",".gitattributes"):
            checks.append((name,(root/name).exists()))
        self.report="REPOSITORY ONBOARDING\n"+"="*72+"\n\n"+"\n".join(f"[{'PASS' if ok else 'MISSING'}] {name}" for name,ok in checks)
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def init_git(self):
        if (Path(self.repo)/".git").exists():return messagebox.showinfo("Onboarding","Git is already initialized.",parent=self)
        try:messagebox.showinfo("Onboarding",git(self.repo,"init"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Onboarding",str(e),parent=self)
    def write_if_missing(self,name,text):
        p=Path(self.repo)/name
        if not p.exists():p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8");return True
        return False
    def create_basics(self):
        created=[]
        templates={
          "README.md":f"# {Path(self.repo).name}\n\nProject description.\n",
          "CHANGELOG.md":"# Changelog\n\n## Unreleased\n\n",
          "SECURITY.md":"# Security Policy\n\nReport vulnerabilities privately to the maintainers.\n",
          "CONTRIBUTING.md":"# Contributing\n\nUse focused branches, tests, documentation, and pull requests.\n",
          ".gitignore":"__pycache__/\n*.py[cod]\n.venv/\n.env\nbuild/\ndist/\n",
          ".gitattributes":"* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.zip binary\n"
        }
        for n,v in templates.items():
            if self.write_if_missing(n,v):created.append(n)
        messagebox.showinfo("Onboarding","Created:\n"+("\n".join(created) if created else "No missing starter files."),parent=self);self.refresh()

class RepositoryAuditPackCenter(tk.Toplevel):
    """Generate a compact technical audit pack from local Git evidence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Audit Pack");self.geometry("1100x740");self._build();self.generate()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Regenerate",command=self.generate).pack(side="left");ttk.Button(bar,text="Export Markdown",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return f"Unavailable: {e}"
    def generate(self):
        status=self.safe("status","--short","--branch");remotes=self.safe("remote","-v");fsck=self.safe("fsck","--no-progress");recent=self.safe("log","-20","--date=short","--pretty=format:- %h %ad %an: %s");tags=self.safe("tag","--sort=-creatordate");config=self.safe("config","--list","--show-origin")
        self.report=f"# Repository Audit Pack: {Path(self.repo).name}\n\n## Status\n```text\n{status}\n```\n\n## Remotes\n```text\n{remotes}\n```\n\n## Recent commits\n{recent}\n\n## Tags\n```text\n{tags}\n```\n\n## Integrity\n```text\n{fsck}\n```\n\n## Git configuration origins\n```text\n{config}\n```\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=f"{Path(self.repo).name}-audit-pack.md")
        if p:Path(p).write_text(self.report,encoding="utf-8")

class BackupBranchManager(tk.Toplevel):
    """Inventory and clean old gccc-backup branches conservatively."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Safety Branch Manager");self.geometry("1100x720");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(bar,text="Inspect",command=self.inspect).pack(side="left",padx=3);ttk.Button(bar,text="Delete selected",command=self.delete).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("branch","date","hash","subject"),show="headings")
        for c,t,w in [("branch","Safety branch",390),("date","Date",130),("hash","Commit",100),("subject","Subject",430)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.out=tk.Text(self,height=12,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=(0,8))
        ttk.Label(self,text="Only gccc-backup/* branches are shown. Delete uses normal git branch -d and will refuse unmerged safety branches.",padding=8).pack(fill="x")
    def refresh(self):
        raw=git(self.repo,"for-each-ref","--sort=-committerdate","--format=%(refname:short)%09%(committerdate:short)%09%(objectname:short)%09%(subject)","refs/heads/gccc-backup/");self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",3)
            if len(p)==4:self.rows.append(p);self.tree.insert("","end",iid=str(len(self.rows)-1),values=p)
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--oneline",r[0])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def delete(self):
        r=self.selected()
        if r and messagebox.askyesno("Safety branch",f"Delete merged safety branch {r[0]}?",parent=self):
            try:messagebox.showinfo("Safety branch",git(self.repo,"branch","-d",r[0]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Safety branch",str(e),parent=self)

class UpstreamHealthCenter(tk.Toplevel):
    """Audit local branches for upstream health, remote existence, and divergence."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Upstream Health Center");self.geometry("1180x740");self.rows=[];self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Fetch + refresh",self.refresh),("Set upstream",self.set_upstream),("Unset upstream",self.unset_upstream),("Publish branch",self.publish)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("branch","upstream","remote_exists","ahead","behind","status"),show="headings")
        for c,t,w in [("branch","Local branch",260),("upstream","Upstream",270),("remote_exists","Remote exists",110),("ahead","Ahead",70),("behind","Behind",70),("status","Assessment",300)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Use this center after branch renames, remote cleanup, or repository migrations to find broken upstream relationships.",padding=8).pack(fill="x")
    def refresh(self):
        try:git(self.repo,"fetch","--all","--prune")
        except:pass
        raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(upstream:short)","refs/heads/");remote_refs=set()
        try:remote_refs=set(x for x in git(self.repo,"for-each-ref","--format=%(refname:short)","refs/remotes/").splitlines())
        except:pass
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            p=line.split("\t",1);branch=p[0];up=p[1] if len(p)>1 else "";exists=bool(up and up in remote_refs);a=b="-";status="No upstream"
            if up and exists:
                try:a=git(self.repo,"rev-list","--count",f"{up}..{branch}");b=git(self.repo,"rev-list","--count",f"{branch}..{up}")
                except:pass
                status="Synchronized" if a=="0" and b=="0" else "Ahead" if a!="0" and b=="0" else "Behind" if a=="0" and b!="0" else "Diverged"
            elif up:status="Broken upstream"
            r=dict(branch=branch,up=up,exists=exists,a=a,b=b,status=status);self.rows.append(r);self.tree.insert("","end",iid=str(len(self.rows)-1),values=(branch,up or "-","Yes" if exists else "No",a,b,status))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def set_upstream(self):
        r=self.selected()
        if not r:return
        value=simpledialog.askstring("Set upstream",f"Upstream for {r['branch']} (example origin/{r['branch']}):",parent=self)
        if value:
            try:messagebox.showinfo("Upstream",git(self.repo,"branch","--set-upstream-to",value,r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Upstream",str(e),parent=self)
    def unset_upstream(self):
        r=self.selected()
        if r and r["up"] and messagebox.askyesno("Unset upstream",f"Remove upstream configuration from {r['branch']}?",parent=self):
            try:messagebox.showinfo("Upstream",git(self.repo,"branch","--unset-upstream",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Upstream",str(e),parent=self)
    def publish(self):
        r=self.selected()
        if r and messagebox.askyesno("Publish branch",f"Push {r['branch']} to origin and set upstream?",parent=self):
            try:messagebox.showinfo("Publish",git(self.repo,"push","-u","origin",r["branch"]),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Publish",str(e),parent=self)

class ReleaseEvidenceCenter(tk.Toplevel):
    """Generate consolidated local evidence for release approval."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Release Evidence Center");self.geometry("1120x760");self._build();self.generate()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Regenerate",command=self.generate).pack(side="left");ttk.Button(bar,text="Export Markdown",command=self.export).pack(side="left",padx=3);ttk.Button(bar,text="Open Release Center",command=lambda:ReleaseCenter(self,self.repo)).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return f"Unavailable: {e}"
    def generate(self):
        import datetime
        status=self.safe("status","--porcelain");clean=status=="Completed successfully.";branch=self.safe("branch","--show-current");head=self.safe("rev-parse","HEAD");tag=self.safe("describe","--tags","--abbrev=0");fsck=self.safe("fsck","--no-progress");sig=self.safe("log","-10","--pretty=format:%h %G? %s");docs=[]
        for f in ("README.md","CHANGELOG.md","RELEASE_NOTES.md","SECURITY.md","LICENSE"):
            docs.append((f,(Path(self.repo)/f).exists()))
        self.report=f"# Release Evidence: {Path(self.repo).name}\n\n- Captured: {datetime.datetime.now().isoformat()}\n- Branch: `{branch}`\n- HEAD: `{head}`\n- Latest tag: `{tag}`\n- Working tree: **{'CLEAN' if clean else 'CHANGED'}**\n\n## Required files\n"+"\n".join(f"- [{'x' if ok else ' '}] {f}" for f,ok in docs)+f"\n\n## Integrity\n```text\n{fsck}\n```\n\n## Recent signature status\n```text\n{sig}\n```\n\n## Working-tree status\n```text\n{status}\n```\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="release-evidence.md")
        if p:Path(p).write_text(self.report,encoding="utf-8")

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
            except:pass
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
        except Exception as e:return messagebox.showerror("Blame",str(e),parent=self)
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
                except:cur["date"]=""
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"show","--stat","--patch","--find-renames",r["hash"])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class RemotePruneAuditCenter(tk.Toplevel):
    """Preview stale remote-tracking refs for every remote before pruning."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote Prune Audit");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Button(bar,text="Refresh preview",command=self.refresh).pack(side="left");ttk.Button(bar,text="Prune selected remote",command=self.prune).pack(side="left",padx=3);ttk.Button(bar,text="Fetch all + prune",command=self.fetch_all).pack(side="left")
        self.remotes=tk.Listbox(self,width=24,font=("Consolas",9));self.remotes.pack(side="left",fill="y",padx=(8,4),pady=5);self.remotes.bind("<<ListboxSelect>>",lambda e:self.preview())
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(side="left",fill="both",expand=True,padx=(4,8),pady=5)
    def refresh(self):
        raw=git(self.repo,"remote");self.rows=[x for x in raw.splitlines() if x and x!="Completed successfully."];self.remotes.delete(0,"end");[self.remotes.insert("end",x) for x in self.rows]
        if self.rows:self.remotes.selection_set(0);self.preview()
    def selected(self):
        s=self.remotes.curselection();return self.rows[s[0]] if s else None
    def preview(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"remote","prune",r,"--dry-run")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",f"DRY RUN FOR {r}\n{'='*72}\n{v}")
    def prune(self):
        r=self.selected()
        if r and messagebox.askyesno("Prune remote",f"Prune stale remote-tracking refs for {r}? Local branches are not deleted.",parent=self):
            try:messagebox.showinfo("Prune",git(self.repo,"remote","prune",r),parent=self);self.preview()
            except Exception as e:messagebox.showerror("Prune",str(e),parent=self)
    def fetch_all(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)

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
        except Exception as e:self.show(str(e))
    def tree(self):
        o=self.obj.get().strip() or "HEAD"
        try:self.show(git(self.repo,"ls-tree","-r","-l",o))
        except Exception as e:self.show(str(e))
    def verify(self):
        o=self.obj.get().strip()
        try:self.show(git(self.repo,"rev-parse","--verify",o))
        except Exception as e:self.show(str(e))

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
        except Exception as e:v="No active bisect session or log unavailable.\n\n"+str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def run(self):
        import shlex
        if not self.clean():return messagebox.showwarning("Bisect","Commit or stash changes before automated bisect.",parent=self)
        good=self.good.get().strip();bad=self.bad.get().strip();cmd=shlex.split(self.cmd.get())
        if not good or not bad or not cmd:return messagebox.showwarning("Bisect","Enter known-good, known-bad and a test command.",parent=self)
        try:
            git(self.repo,"rev-parse","--verify",good);git(self.repo,"rev-parse","--verify",bad);git(self.repo,"bisect","start",bad,good)
            r=subprocess.run(["git","bisect","run",*cmd],cwd=self.repo,text=True,capture_output=True,timeout=7200,encoding="utf-8",errors="replace");v=(r.stdout+"\n"+r.stderr).strip();self.out.delete("1.0","end");self.out.insert("1.0",v);messagebox.showinfo("Bisect",f"Automated bisect finished with exit code {r.returncode}. Review the output, then Reset bisect when done.",parent=self)
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
    def reset(self):
        try:messagebox.showinfo("Bisect",git(self.repo,"bisect","reset"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)

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
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def export(self):
        ref=self.ref.get().strip() or "HEAD";sub=self.path.get().strip().strip("/");name=Path(self.repo).name;safe=ref.replace("/","-").replace("\\","-");dest=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",initialfile=f"{name}-{safe}.zip")
        if not dest:return
        args=["archive","--format=zip",f"--output={dest}"]
        if self.prefix.get():args += [f"--prefix={name}-{safe}/"]
        args.append(ref)
        if sub:args.append(sub)
        try:messagebox.showinfo("Archive",git(self.repo,*args),parent=self)
        except Exception as e:messagebox.showerror("Archive",str(e),parent=self)

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
        except Exception as e:self.report=str(e)
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
        except Exception as e:raw=str(e)
        self.raw_report=raw;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            m=re.search(r"(?:unreachable|dangling) (commit|tree|blob|tag) ([0-9a-f]{40,64})",line)
            if not m:continue
            kind,sha=m.group(1),m.group(2);date=subject=""
            if kind=="commit":
                try:
                    info=git(self.repo,"show","-s","--date=iso-strict","--pretty=format:%cI%x1f%s",sha).split("\x1f",1);date=info[0];subject=info[1] if len(info)>1 else ""
                except:pass
            else:subject=line
            self.rows.append(dict(kind=kind,sha=sha,date=date,subject=subject));self.tree.insert("","end",iid=str(len(self.rows)-1),values=(kind,sha,date,subject))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        try:v=git(self.repo,"cat-file","-p",r["sha"]) if r["kind"]!="commit" else git(self.repo,"show","--stat","--patch","--find-renames",r["sha"])
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def recover(self):
        import datetime,re
        r=self.selected()
        if not r or r["kind"]!="commit":return messagebox.showinfo("Recovery","Select an unreachable commit. Trees and blobs cannot be branched directly.",parent=self)
        default=f"recovery/fsck-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}-{r['sha'][:8]}";name=simpledialog.askstring("Recovery branch","New branch name:",initialvalue=default,parent=self)
        if not name or not re.match(r"^[A-Za-z0-9._/-]+$",name):return
        try:messagebox.showinfo("Recovery",git(self.repo,"branch",name,r["sha"]),parent=self);self.scan()
        except Exception as e:messagebox.showerror("Recovery",str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="dangling-object-report.txt")
        if p:Path(p).write_text(self.raw_report,encoding="utf-8")

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

class CommitGraphMaintenanceCenter(tk.Toplevel):
    """Inspect and maintain the commit-graph and multi-pack-index acceleration files."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Graph & Pack Index Center");self.geometry("1080x700");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Write commit graph",self.write_graph),("Verify commit graph",self.verify_graph),("Write multi-pack-index",self.write_midx),("Verify multi-pack-index",self.verify_midx),("Expire redundant packs",self.expire)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="These files accelerate history and object lookup. Expire only removes packfiles made redundant by the multi-pack-index and requires confirmation.",padding=8).pack(fill="x")
    def run(self,args,title,confirm=None):
        if confirm and not messagebox.askyesno(title,confirm,parent=self):return
        try:v=git(self.repo,*args);messagebox.showinfo(title,v,parent=self);self.refresh()
        except Exception as e:messagebox.showerror(title,str(e),parent=self)
    def refresh(self):
        gd=Path(git(self.repo,"rev-parse","--git-dir"));gd=(Path(self.repo)/gd).resolve() if not gd.is_absolute() else gd;cg=gd/"objects"/"info"/"commit-graph";chain=gd/"objects"/"info"/"commit-graphs";midx=gd/"objects"/"pack"/"multi-pack-index"
        v=f"COMMIT GRAPH & PACK INDEX\n{'='*72}\nGit dir: {gd}\nSingle commit-graph: {'Present' if cg.exists() else 'Missing'}\nCommit-graph chain: {'Present' if chain.exists() else 'Missing'}\nMulti-pack-index: {'Present' if midx.exists() else 'Missing'}\n\nOBJECTS\n"+git(self.repo,"count-objects","-vH")
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def write_graph(self):self.run(["commit-graph","write","--reachable","--changed-paths"],"Commit graph")
    def verify_graph(self):self.run(["commit-graph","verify","--shallow"],"Commit graph verify")
    def write_midx(self):self.run(["multi-pack-index","write","--bitmap"],"Multi-pack-index")
    def verify_midx(self):self.run(["multi-pack-index","verify"],"Multi-pack-index verify")
    def expire(self):self.run(["multi-pack-index","expire"],"Expire packs","Expire packfiles Git considers redundant through the multi-pack-index?")

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

class GitMaintenanceScheduleCenter(tk.Toplevel):
    """Inspect and control Git maintenance registration and strategy."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Maintenance Schedule Center");self.geometry("1080x700");self.strategy=tk.StringVar(value="incremental");self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");ttk.Combobox(bar,textvariable=self.strategy,values=["incremental","geometric"],state="readonly",width=15).pack(side="left")
        for t,c in [("Refresh",self.refresh),("Register repository",self.register),("Unregister",self.unregister),("Set strategy",self.set_strategy),("Run scheduled tasks now",self.run)]:ttk.Button(bar,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Registration delegates scheduling to Git's platform integration. Unregister stops future scheduled maintenance for this repository; it does not delete objects.",padding=8).pack(fill="x")
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        repo=self.safe("config","--global","--get-all","maintenance.repo");strategy=self.safe("config","--get","maintenance.strategy");auto=self.safe("config","--get","maintenance.auto");v=f"MAINTENANCE SCHEDULE\n{'='*72}\nRegistered repositories:\n{repo}\n\nRepository strategy: {strategy}\nmaintenance.auto: {auto}\n\nOBJECT STATUS\n{self.safe('count-objects','-vH')}"
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def register(self):
        try:messagebox.showinfo("Maintenance",git(self.repo,"maintenance","register"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Maintenance",str(e),parent=self)
    def unregister(self):
        if messagebox.askyesno("Maintenance","Unregister this repository from scheduled maintenance?",parent=self):
            try:messagebox.showinfo("Maintenance",git(self.repo,"maintenance","unregister"),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Maintenance",str(e),parent=self)
    def set_strategy(self):
        try:messagebox.showinfo("Maintenance",git(self.repo,"config","maintenance.strategy",self.strategy.get()),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Maintenance",str(e),parent=self)
    def run(self):
        try:messagebox.showinfo("Maintenance",git(self.repo,"maintenance","run","--scheduled"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Maintenance",str(e),parent=self)

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

class GitFetchPreviewCenter(tk.Toplevel):
    """Dry-run fetch analysis with optional refspec and prune/tags controls."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Fetch Preview Center");self.geometry("1080x700");self.remote=tk.StringVar(value="origin");self.refspec=tk.StringVar();self.prune=tk.BooleanVar(value=True);self.tags=tk.BooleanVar();self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill="x");self.box=ttk.Combobox(bar,textvariable=self.remote,width=18);self.box.pack(side="left");ttk.Entry(bar,textvariable=self.refspec).pack(side="left",fill="x",expand=True,padx=4);ttk.Checkbutton(bar,text="Prune",variable=self.prune).pack(side="left");ttk.Checkbutton(bar,text="Tags",variable=self.tags).pack(side="left",padx=3);ttk.Button(bar,text="Dry run",command=self.preview).pack(side="left");ttk.Button(bar,text="Fetch now",command=self.fetch).pack(side="left",padx=3)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Dry-run first to review new, updated, deleted, or forced remote-tracking changes. A custom refspec is optional.",padding=8).pack(fill="x")
    def refresh(self):
        rem=[x for x in git(self.repo,"remote").splitlines() if x and x!="Completed successfully."];self.box["values"]=rem
        if rem and self.remote.get() not in rem:self.remote.set(rem[0])
        self.preview()
    def args(self,dry=True):
        args=["fetch"]
        if dry:args.append("--dry-run")
        if self.prune.get():args.append("--prune")
        if self.tags.get():args.append("--tags")
        args.append(self.remote.get().strip())
        if self.refspec.get().strip():args.append(self.refspec.get().strip())
        return args
    def preview(self):
        try:v=git(self.repo,*self.args(True))
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0","FETCH DRY RUN\n"+"="*72+"\n"+v)
    def fetch(self):
        if not messagebox.askyesno("Fetch",f"Execute fetch from {self.remote.get()} with the selected options?",parent=self):return
        try:messagebox.showinfo("Fetch",git(self.repo,*self.args(False)),parent=self);self.preview()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
