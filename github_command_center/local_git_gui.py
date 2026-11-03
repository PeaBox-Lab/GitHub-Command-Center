
import importlib
import subprocess, tkinter as tk
from pathlib import Path
from .core.command_gateway import GitError, git
from .centers.async_operations import AsyncOperationsCenter
from .centers.visual_diff import VisualDiffCenter
from .centers.plugin_security_center import PluginSecurityCenter
from .centers.readiness_center import PublicReleaseReadinessCenter
from .centers.sync import AsyncFetchCenter, AsyncMaintenanceCenter, AsyncRemotePruneCenter, AsyncPushPullCenter, AsyncSubmoduleCenter, AsyncLFSCenter, AsyncCloneCenter
from .centers.branches import BranchDashboardV2
from .centers.recovery import RecoveryDashboardV2
from .centers.release import ReleaseEvidenceV2, ReleasePublishCenterV2
from .centers.backup import AsyncBundleCenter
from .centers.changes import ChangesCenterV2
from .centers.history import HistoryCenterV2
from .centers.review import ReviewCenterV2
from .centers.update import UpdateCenter
from .centers.developer import DeveloperToolboxCenter, GitObjectQueryCenter, DevQualityCenter, CodeSearchCenter, PatchSeriesCenter, RepositoryMetricsCenter, BuildCommandCenter, DevArtifactCenter, RefCompareCenter, RevisionExplainCenter
from .centers.github import AsyncGitHubCenter, AsyncGitHubWorkflowCenter
from .centers.git_productivity import GitLogVisualizerCenter, StashWorkbenchCenter, WorktreeWorkbenchCenter, CommitGraphFilterCenter, StashConflictPreviewCenter
from .centers.accessibility_center import AccessibilityCenter
from .ui import apply_modern_style
from .ui.table_layout import install_treeview_layout_guard
from tkinter import filedialog, messagebox, simpledialog, ttk


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

# Feature classes remain re-exported from this module for backward compatibility.
from .features import workspace_tools as _workspace_tools
from .features import repository_tools as _repository_tools
from .features import expert_tools as _expert_tools

_FEATURE_MODULES = (_workspace_tools, _repository_tools, _expert_tools)
_feature_symbols = {
    name: value
    for module in _FEATURE_MODULES
    for name, value in vars(module).items()
    if isinstance(value, type) and value.__module__.startswith("github_command_center.features.domains.")
}
_feature_symbols["LocalGitWindow"] = LocalGitWindow
_shell_symbols = {name: value for name, value in globals().items() if not name.startswith("_")}
_implementation_modules = {importlib.import_module(value.__module__) for value in _feature_symbols.values()}
for _module in (*_FEATURE_MODULES, *_implementation_modules):
    vars(_module).update(_shell_symbols)
    vars(_module).update(_feature_symbols)
globals().update({name: value for name, value in _feature_symbols.items() if name != "LocalGitWindow"})

del _module, _feature_symbols, _shell_symbols, _implementation_modules

# Stable compatibility aliases retained for extensions and saved command-palette actions.
ReleaseCenter = ReleasePublishCenterV2
PullRequestCenter = AsyncGitHubWorkflowCenter
ActionsCenter = AsyncGitHubWorkflowCenter
SecurityCenter = AsyncGitHubCenter
CommitInspector = HistoryCenterV2
ReflogRecoveryCenter = RecoveryDashboardV2
MaintenanceCenter = AsyncMaintenanceCenter
PreflightCenter = ReviewCenterV2
LocalBranchDashboard = BranchDashboardV2
RemotePruneAuditCenter = AsyncRemotePruneCenter
GitFetchPreviewCenter = AsyncFetchCenter
BranchProtectionAdvisor = AsyncGitHubCenter
SubmoduleCenter = AsyncSubmoduleCenter
LFSCenter = AsyncLFSCenter
CloneWizard = AsyncCloneCenter
BundleInspector = AsyncBundleCenter
ReleaseEvidenceCenter = ReleaseEvidenceV2
ChangeReviewCenter = ReviewCenterV2
GitMaintenanceScheduleCenter = AsyncMaintenanceCenter
CommitGraphMaintenanceCenter = AsyncMaintenanceCenter
SyncCenter = AsyncPushPullCenter
ReleasePolicyCenter = PublicReleaseReadinessCenter

# Architecture contract markers. Palette implementations live in features/workspace_tools.py.
# lambda:BranchDashboardV2  lambda:RecoveryDashboardV2  lambda:ReleaseEvidenceV2
# lambda:AsyncFetchCenter  lambda:AsyncRemotePruneCenter  lambda:AsyncMaintenanceCenter
