"""Bounded feature domain for GitHub Command Center v3.74."""
import csv
import datetime
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ...core.command_gateway import GitError, git

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
            ("Advanced Git operations",lambda:AdvancedGitWindow(self,repo),"rebase cherry-pick reset ignore"),("Release Center",lambda:ReleasePublishCenterV2(self,repo),"release tag assets bundle"),
            ("Pull Request Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"pull request pr review merge"),("GitHub Actions Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"workflow actions ci logs"),
            ("Security Center",lambda:SecurityCenter(self,repo),"dependabot code secret scan checksums"),("Repository Health",lambda:RepositoryHealthCenter(self,repo),"quality docs governance score"),
            ("Worktree Center",lambda:WorktreeCenter(self,repo),"parallel branches worktrees"),("Compare & Review",lambda:RepositoryCompareCenter(self,repo),"compare branch tag diff"),
            ("Backup & Recovery",lambda:BackupRestoreCenter(self,repo),"bundle restore checkpoint"),("Repository Manager",lambda:RepositoryManager(self,repo),"multiple repositories portfolio"),
            ("Diagnostics",lambda:SettingsDiagnosticsCenter(self,repo),"environment git python configuration"),("Smart Sync",lambda:SyncCenter(self,repo),"fetch pull push ahead behind"),
            ("Repository Search",lambda:SearchCenter(self,repo),"grep commit file search"),("Pre-Commit Review",lambda:ReviewCenterV2(self,repo),"stage checks diff commit"),
            ("Repository Notes",lambda:RepositoryNotesCenter(self,repo),"private notes decisions"),("Branch Cleanup",lambda:BranchCleanupCenter(self,repo),"merged stale prune"),
            ("Project Snapshot",lambda:ProjectSnapshotCenter(self,repo),"handover snapshot markdown"),("Patch Center",lambda:PatchCenter(self,repo),"patch apply format-patch"),
            ("Regression Finder",lambda:BisectCenter(self,repo),"bisect regression"),("Commit Inspector",lambda:HistoryCenterV2(self,repo),"blame file history commit"),
            ("Submodule Center",lambda:SubmoduleCenter(self,repo),"submodule recursive"),("Repository Tasks",lambda:TaskCenter(self,repo),"checklist tasks"),
            ("Archive & Handover",lambda:ArchiveCenter(self,repo),"zip bundle support pack"),("Git Hooks Manager",lambda:HooksCenter(self,repo),"hooks pre-commit commit-msg"),
            ("Git LFS Center",lambda:LFSCenter(self,repo),"large files lfs track"),("Automation Recipes",lambda:AutomationCenter(self,repo),"automation recipes checks"),("Identity & Signing",lambda:IdentitySigningCenter(self,repo),"identity email gpg sign verify"),("Commit Message Studio",lambda:CommitMessageStudio(self,repo),"conventional commits message"),("Changelog Studio",lambda:ChangelogStudio(self,repo),"changelog release notes commits"),("Remote Migration & Mirror",lambda:RemoteMigrationCenter(self,repo),"remote backup mirror migration"),("Credential & Remote Hygiene",lambda:CredentialAuditCenter(self,repo),"credentials helper url ssh https auth"),("Release Policy Center",lambda:ReleasePolicyCenter(self,repo),"release policy gates semver version"),("Repository Metrics",lambda:RepositoryMetricsCenter(self,repo),"metrics contributors languages commits activity"),("Plugin Manager",lambda:PluginManager(self,repo),"plugins extensions commands"),("Batch Operations",lambda:BatchOperationsCenter(self,repo),"batch multiple repositories portfolio"),("Operations Dashboard",lambda:RepositoryDashboardCenter(self,repo),"dashboard operational status next action"),("Repository Data Export",lambda:DataExportCenter(self,repo),"export json csv commits metadata"),("Background Jobs",lambda:BackgroundJobsCenter(self,repo),"jobs queue background cancel logs"),("Preferences",lambda:PreferencesCenter(self,repo),"preferences theme appearance defaults"),("Portfolio History",lambda:PortfolioHistoryCenter(self,repo),"sqlite portfolio history snapshots trends"),("Self-Test & Readiness",lambda:SelfTestCenter(self,repo),"self test readiness smoke diagnostics"),("Partial Staging",lambda:PartialStagingCenter(self,repo),"partial stage hunk line add patch"),("Reflog Recovery",lambda:RecoveryDashboardV2(self,repo),"reflog recover lost commit reset checkout branch"),("Interactive Rebase Editor",lambda:InteractiveRebaseEditor(self,repo),"interactive rebase squash fixup reword edit drop reorder"),("Unified Ref Browser",lambda:UnifiedRefBrowser(self,repo),"refs branches remotes tags stash notes"),("Repository History Browser",lambda:RepositoryHistoryBrowser(self,repo),"history browse tree file commit export"),("Sparse Checkout",lambda:SparseCheckoutCenter(self,repo),"sparse checkout cone large repository folders"),("Repository Maintenance",lambda:AsyncMaintenanceCenter(self,repo),"maintenance gc fsck objects commit graph"),("Git Notes",lambda:GitNotesCenter(self,repo),"git notes annotation metadata commit"),("Diff & Merge Tools",lambda:DiffMergeToolCenter(self,repo),"difftool mergetool vscode winmerge beyond compare kdiff3"),("Recorded Conflict Resolution",lambda:RerereCenter(self,repo),"rerere recorded resolution recurring conflict"),("Remote Branch Center",lambda:RemoteBranchCenter(self,repo),"remote branch track publish rename delete"),("Ignore & Attributes Studio",lambda:IgnoreAttributesStudio(self,repo),"gitignore gitattributes check-ignore attributes"),("Advanced Clone Wizard",lambda:CloneWizard(self),"clone shallow depth partial single branch blob filter"),("Worktree Safety",lambda:WorktreeSafetyCenter(self,repo),"worktree safety lock unlock prune"),("Repository Doctor",lambda:RepositoryDoctor(self,repo),"doctor diagnose repair status config integrity"),("Tag & Release Audit",lambda:TagReleaseAuditCenter(self,repo),"tags release audit signature remote annotated lightweight"),("Stash Manager Pro",lambda:StashManagerPro(self,repo),"stash apply pop branch drop untracked"),("Safe Clean Center",lambda:CleanPreviewCenter(self,repo),"clean untracked ignored preview delete"),("Repository Size Explorer",lambda:RepositorySizeCenter(self,repo),"size large files objects lfs storage"),("Force-with-Lease Safety",lambda:ForcePushSafetyCenter(self,repo),"force with lease rewritten history push safety"),("Advanced History Search",lambda:CommitSearchPro(self,repo),"pickaxe regex history search content"),("Git Bundle Inspector",lambda:BundleInspector(self,repo),"bundle verify heads clone restore backup"),("Branch Protection Advisor",lambda:BranchProtectionAdvisor(self,repo),"branch protection rules review checks github"),("Repository Favorites",lambda:RepositoryFavoritesCenter(self,repo),"favorites groups repositories portfolio"),("Async Git Operations",lambda:AsyncOperationsCenter(self,repo),"async background fetch fsck maintenance gc cancel progress"),("Changes Center V2",lambda:ChangesCenterV2(self,repo),"changes stage unstage commit discard diff"),("History Center V2",lambda:HistoryCenterV2(self,repo),"history log commit inspect grep refs"),("GitHub Network Center",lambda:AsyncGitHubCenter(self,repo),"github async api pr issue actions release security"),("GitHub Workflow Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"github pr checks merge issue workflow rerun async"),("Review Center V2",lambda:ReviewCenterV2(self,repo),"review preflight tests compile ruff bandit diff"),("Release Publish Center V2",lambda:ReleasePublishCenterV2(self,repo),"release tag push publish github assets notes"),("Push & Pull Center",lambda:AsyncPushPullCenter(self,repo),"async push pull rebase ff force lease upstream"),("Submodule Center V2",lambda:AsyncSubmoduleCenter(self,repo),"submodule async add sync update init"),("Git LFS Center V2",lambda:AsyncLFSCenter(self,repo),"lfs async track fetch pull prune"),("Clone Center V2",lambda:AsyncCloneCenter(self,repo),"clone async shallow partial filter"),("Git Bundle Center",lambda:AsyncBundleCenter(self,repo),"bundle backup verify list heads async"),("Visual Diff Center",lambda:VisualDiffCenter(self,repo),"visual side by side word diff hunk stage unstage"),("Plugin Security Center",lambda:PluginSecurityCenter(self,repo),"plugin security manifest permissions allowlist publisher trust signature hash"),("Public Release Readiness",lambda:PublicReleaseReadinessCenter(self,repo),"public release readiness audit score gates"),("Verified Update Center",lambda:UpdateCenter(self,repo,"3.61.0"),"update verify sha256 metadata version installer"),("Developer Toolbox",lambda:DeveloperToolboxCenter(self,repo),"developer patch whitespace changed files commit diagnostics"),("Developer Quality",lambda:DevQualityCenter(self,repo),"developer test lint security compile quality"),("Code Search",lambda:CodeSearchCenter(self,repo),"developer code search grep history regex"),("Patch Series",lambda:PatchSeriesCenter(self,repo),"patch series format patch export"),("Repository Metrics",lambda:RepositoryMetricsCenter(self,repo),"repository metrics files commits contributors objects"),("Build & Validation Runner",lambda:BuildCommandCenter(self,repo),"developer build test compile quality"),("Developer Artifacts",lambda:DevArtifactCenter(self,repo),"developer source archive manifest export"),("Git Log Visualizer",lambda:GitLogVisualizerCenter(self,repo),"git log visualization graph branches commits refs"),("Stash Workbench",lambda:StashWorkbenchCenter(self,repo),"stash manager preview apply pop branch selective"),("Worktree Workbench",lambda:WorktreeWorkbenchCenter(self,repo),"worktree manager add lock move remove prune"),("Interactive Commit Graph",lambda:CommitGraphFilterCenter(self,repo),"git log graph filters author date merges path refs"),("Stash Diff & Conflict Preview",lambda:StashConflictPreviewCenter(self,repo),"stash diff conflict preview merge tree risk"),("Ref Compare",lambda:RefCompareCenter(self,repo),"developer compare refs branches commits diff"),("Revision Explain",lambda:RevisionExplainCenter(self,repo),"developer revision explain object ref metadata"),("Git Object Query",lambda:GitObjectQueryCenter(self,repo),"git object cat file tree blob path verify"),("Accessibility & Display",lambda:AccessibilityCenter(self,repo),"accessibility high contrast large text keyboard focus reduce motion"),("Preflight Quality Gates",lambda:ReviewCenterV2(self,repo),"preflight quality gates push pr release checks"),("Commit Template Center",lambda:CommitTemplateCenter(self,repo),"commit template message conventional"),("Patch Queue Center",lambda:PatchQueueCenter(self,repo),"patch queue git am mailbox continue abort"),("Hook Audit Center",lambda:HookAuditCenter(self,repo),"hooks audit executable provenance precommit"),("Merge Preview Center",lambda:MergePreviewCenter(self,repo),"merge preview merge-tree conflict impact"),("Reset & Recovery Planner",lambda:ResetRecoveryPlanner(self,repo),"reset soft mixed hard recovery backup"),("Git Configuration Center",lambda:GitConfigCenter(self,repo),"git config local global origin scope"),("Cherry-Pick Queue",lambda:CherryPickQueueCenter(self,repo),"cherry pick queue commits continue abort"),("Release Asset Integrity",lambda:ReleaseAssetIntegrityCenter(self,repo),"release asset sha256 checksum verify"),("Local Release Archive",lambda:LocalReleaseArchiveCenter(self,repo),"release archive source zip bundle checksums metadata"),("Signature Audit",lambda:CommitSignatureAuditCenter(self,repo),"signature audit signed commits verification gpg"),("Release Comparison",lambda:ReleaseCompareCenter(self,repo),"release compare tags commits files diff"),("Safe Branch Delete",lambda:SafeDeleteBranchWizard(self,repo),"safe branch delete merged worktree upstream"),("Pull Strategy Advisor",lambda:PullRebaseAdvisor(self,repo),"pull strategy merge rebase fast forward ahead behind"),("Detached HEAD Recovery",lambda:DetachedHeadRecoveryCenter(self,repo),"detached head recovery branch switch"),("Repository State Export",lambda:RepositoryStateExportCenter(self,repo),"repository state export json markdown audit"),("Repository Rules Audit",lambda:RepositoryRulesCenter(self,repo),"repository rules governance docs codeowners workflows"),("Commit Range Exporter",lambda:CommitRangeExporter(self,repo),"commit range patches bundle markdown export"),("Local Branch Dashboard",lambda:BranchDashboardV2(self,repo),"branch dashboard divergence recency compare"),("Repository Onboarding",lambda:RepositoryOnboardingCenter(self,repo),"repository onboarding starter readme governance"),("Repository Audit Pack",lambda:RepositoryAuditPackCenter(self,repo),"audit pack evidence status remotes fsck config"),("Safety Branch Manager",lambda:BackupBranchManager(self,repo),"backup safety branch gccc cleanup recovery"),("Upstream Health",lambda:UpstreamHealthCenter(self,repo),"upstream health broken branch remote divergence"),("Release Evidence",lambda:ReleaseEvidenceV2(self,repo),"release evidence approval integrity signature docs"),("Repository Locator",lambda:RepositoryLocatorCenter(self,repo),"repository locator scan workspace find repositories"),("Blame Explorer",lambda:BlameExplorerCenter(self,repo),"blame line author commit inspector"),("Remote Prune Audit",lambda:AsyncRemotePruneCenter(self,repo),"remote prune stale refs dry run"),("Git Object Inspector",lambda:CommitObjectCenter(self,repo),"git object cat-file tree plumbing inspect"),("Automated Bisect",lambda:BisectAutomationCenter(self,repo),"bisect run regression automated test command"),("Revision Archive",lambda:RevisionArchiveCenter(self,repo),"archive revision zip subdirectory export"),("Commit Metadata Inspector",lambda:CommitMetadataCenter(self,repo),"commit metadata author committer parents signature tree"),("Dangling Object Recovery",lambda:DanglingObjectRecoveryCenter(self,repo),"dangling unreachable commit fsck recovery lost objects"),("Contributor Mailmap",lambda:MailmapCenter(self,repo),"mailmap contributors identities author email canonical"),("Patch Identity Comparator",lambda:PatchIdCenter(self,repo),"patch id duplicate cherry equivalent rebased commit"),("Credential Redaction Audit",lambda:CredentialRedactionAuditCenter(self,repo),"credential secret token redaction audit security"),("Ref Consistency",lambda:RefConsistencyCenter(self,repo),"ref consistency symbolic head connectivity refs"),("Release Branch Planner",lambda:ReleaseBranchPlanner(self,repo),"release branch planner create base switch"),("Switch & Restore",lambda:GitSwitchRestoreCenter(self,repo),"git switch restore source staged worktree"),("Rebase State Inspector",lambda:RebaseStateCenter(self,repo),"rebase state todo continue skip abort conflicts"),("Git Describe & Version",lambda:GitDescribeCenter(self,repo),"git describe version tag dirty release"),("Worktree Repair",lambda:GitWorktreeRepairCenter(self,repo),"worktree repair prune stale metadata"),("Tag Manager Pro",lambda:TagManagerPro(self,repo),"tag annotated signed push verify delete remote"),("Pathspec Explorer",lambda:GitPathspecCenter(self,repo),"pathspec glob exclude files changed preview"),("Git Grep Studio",lambda:GitGrepStudio(self,repo),"grep repository regex fixed historical content search"),("Tree Comparison",lambda:ArchiveCompareCenter(self,repo),"tree compare dirstat rename files refs"),("Remote URL Audit",lambda:RemoteUrlAuditCenter(self,repo),"remote url fetch push fork upstream audit"),("Git Replace Center",lambda:GitReplaceCenter(self,repo),"git replace object local ref graft"),("Merge Base Explorer",lambda:MergeBaseExplorer(self,repo),"merge base fork point ancestor independent"),("Commit Reachability Explorer",lambda:BranchContainsCenter(self,repo),"branch contains tag contains no merged reachability"),("Revert Queue",lambda:RevertQueueCenter(self,repo),"revert queue commits continue abort backup"),("Git Log Query Builder",lambda:GitLogQueryCenter(self,repo),"git log author date path grep merges query"),("Git Index Inspector",lambda:IndexInspectorCenter(self,repo),"index staging area stages blobs flags unstage"),("Merge Commit Revert",lambda:MergeCommitRevertCenter(self,repo),"merge commit revert mainline parent protected"),("Commit Graph & Pack Index",lambda:CommitGraphMaintenanceCenter(self,repo),"commit graph multi pack index bitmap maintenance"),("Diff Algorithm Lab",lambda:DiffAlgorithmCenter(self,repo),"diff algorithm myers patience histogram minimal word diff"),("Git Subtree Center",lambda:SubtreeCenter(self,repo),"git subtree vendor split add pull push"),("History Rewrite Advisor",lambda:GitFilterRepoAdvisor(self,repo),"filter repo history rewrite remove secret large file"),("Attributes Audit",lambda:AttributesAuditCenter(self,repo),"gitattributes audit binary lfs text eol diff merge"),("Range-Diff Center",lambda:GitRangeDiffCenter(self,repo),"range diff rebase patch series compare"),("Refspec Lab",lambda:RefspecLabCenter(self,repo),"refspec fetch push dry run remote mapping"),("Git Notes Merge",lambda:GitNotesMergeCenter(self,repo),"git notes merge union manual ours theirs"),("Merge Strategy Lab",lambda:MergeStrategyLabCenter(self,repo),"merge strategy ort recursive ours theirs subtree preview"),("Config Include Inspector",lambda:ConfigIncludeCenter(self,repo),"git config include includeif origins scopes"),("Pack Inventory",lambda:PackInventoryCenter(self,repo),"pack inventory verify-pack large blobs objects"),("Change Statistics",lambda:ChangeStatisticsCenter(self,repo),"change statistics churn authors extensions range"),("Conflict Stage Explorer",lambda:ConflictStageExplorer(self,repo),"conflict stages base ours theirs index"),("Branch Rename Planner",lambda:BranchRenamePlanner(self,repo),"branch rename remote upstream protected"),("Lost & Found Center",lambda:LostFoundCenter(self,repo),"lost found fsck recovery commit object"),("Shallow Repository Center",lambda:ShallowRepositoryCenter(self,repo),"shallow clone deepen unshallow history tags"),("Status Porcelain Explorer",lambda:StatusPorcelainCenter(self,repo),"status porcelain v2 automation records"),("Sparse Index Center",lambda:GitSparseIndexCenter(self,repo),"sparse index checkout performance large repository"),("Maintenance Schedule",lambda:GitMaintenanceScheduleCenter(self,repo),"maintenance schedule register strategy incremental geometric"),("Repository Format Inspector",lambda:ObjectFormatCenter(self,repo),"repository format sha1 sha256 ref storage extensions compatibility"),("Selective Clean",lambda:GitCleanInteractiveCenter(self,repo),"clean selective untracked ignored preview"),("File Evolution",lambda:FileEvolutionCenter(self,repo),"file evolution history rename content export"),("Remote Details",lambda:GitRemoteShowCenter(self,repo),"remote show tracking stale branches details"),("Protocol Diagnostics",lambda:ProtocolDiagnosticsCenter(self,repo),"git protocol v2 packet trace remote capabilities"),("Object Alternates Inspector",lambda:AlternatesInspectorCenter(self,repo),"object alternates shared clone dissociate repack"),("EOL Normalization",lambda:EolNormalizationCenter(self,repo),"eol line ending autocrlf gitattributes renormalize"),("Commit Message Audit",lambda:CommitMessageAuditCenter(self,repo),"commit message audit conventional quality subject"),("Revision Manifest",lambda:GitArchiveManifestCenter(self,repo),"revision manifest tree blob verify archive integrity"),("Branch Descriptions",lambda:BranchDescriptionCenter(self,repo),"branch description config local metadata purpose"),("Selective Stash",lambda:SelectiveStashCenter(self,repo),"stash selective pathspec keep index untracked"),("Worktree Move",lambda:WorktreeMoveCenter(self,repo),"worktree move relocate repair linked"),("Config Snapshot Compare",lambda:ConfigSnapshotCompareCenter(self,repo),"git config snapshot compare diff origin scope"),("Fixup & Squash Commits",lambda:CommitFixupCenter(self,repo),"fixup squash amend autosquash staged commit"),("Tracked File Flags",lambda:TrackedFileFlagsCenter(self,repo),"assume unchanged skip worktree update index flags"),("Revision Walk Lab",lambda:RevisionWalkCenter(self,repo),"revision walk topology ancestry first parent boundary order"),("Show-Branch Explorer",lambda:GitShowBranchCenter(self,repo),"show branch topology comparison multiple refs"),("Name-Rev Explorer",lambda:GitNameRevCenter(self,repo),"name rev human readable commit object tags"),("Object Growth Tracker",lambda:GitCountObjectsTrendCenter(self,repo),"count objects growth trend packs garbage maintenance"),("Ref Verification",lambda:GitVerifyRefCenter(self,repo),"verify ref symbolic peel reflog object"),("Ignore Rule Batch Tester",lambda:GitCheckIgnoreBatchCenter(self,repo),"check ignore batch verbose provenance patterns"),("Fetch Preview",lambda:AsyncFetchCenter(self,repo),"fetch dry run prune tags refspec preview")]
        self.render()
    def render(self):
        q=self.q.get().lower().strip();self.filtered=[c for c in self.commands if not q or q in (c[0]+" "+c[2]).lower()];self.list.delete(0,"end")
        for name,_,tags in self.filtered:self.list.insert("end",f"{name}    [{tags}]")
        if self.filtered:self.list.selection_set(0)
    def launch(self):
        s=self.list.curselection()
        if s:self.filtered[s[0]][1]();self.destroy()
