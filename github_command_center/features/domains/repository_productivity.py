"""Bounded Git feature domain."""
import csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys, tempfile, threading, time, tkinter as tk, zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ...core.command_gateway import GitError, git
from ...core.error_boundary import HANDLED_EXCEPTIONS, report_error

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
        except HANDLED_EXCEPTIONS as e:v=str(e)
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
        except HANDLED_EXCEPTIONS:self.rows=[]
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
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Commit template",str(e),parent=self)
    def disable(self):
        try:git(self.repo,"config","--unset","commit.template");messagebox.showinfo("Commit template","Repository commit template configuration removed.",parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Commit template",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:self.out.delete("1.0","end");self.out.insert("1.0",str(e));messagebox.showwarning("Patch queue","Patch application paused or failed. Resolve conflicts, then Continue/Skip/Abort.",parent=self)
    def control(self,arg):
        try:messagebox.showinfo("Patch queue",git(self.repo,"am",arg),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Patch queue",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Hook",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:summary=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",summary)
    def merge(self):
        t=self.target.get().strip()
        if not t:return
        if git(self.repo,"status","--porcelain")!="Completed successfully.":return messagebox.showwarning("Merge","Commit or stash changes before merging.",parent=self)
        if messagebox.askyesno("Merge",f"Merge {t} into the current branch?",parent=self):
            try:messagebox.showinfo("Merge",git(self.repo,"merge","--no-edit",t),parent=self)
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Merge",str(e),parent=self)
    def abort(self):
        try:messagebox.showinfo("Merge",git(self.repo,"merge","--abort"),parent=self)
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Merge",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def execute(self):
        import datetime
        t=self.target.get().strip();mode=self.mode.get()
        try:git(self.repo,"rev-parse",t)
        except HANDLED_EXCEPTIONS as e:return messagebox.showerror("Reset",str(e),parent=self)
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
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Reset",str(e),parent=self)

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
        except HANDLED_EXCEPTIONS as e:self.report=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",self.report)
    def set_value(self):
        k=self.key.get().strip();v=self.value.get()
        if not k:return
        if self.scope.get()=="--global" and not messagebox.askyesno("Global Git config",f"Set global {k} for the current user?",parent=self):return
        try:messagebox.showinfo("Git config",git(self.repo,"config",self.scope.get(),k,v),parent=self);self.refresh()
        except HANDLED_EXCEPTIONS as e:messagebox.showerror("Git config",str(e),parent=self)
    def unset(self):
        k=self.key.get().strip()
        if not k:return
        if messagebox.askyesno("Unset config",f"Unset {k} at {self.scope.get()} scope?",parent=self):
            try:messagebox.showinfo("Git config",git(self.repo,"config",self.scope.get(),"--unset-all",k),parent=self);self.refresh()
            except HANDLED_EXCEPTIONS as e:messagebox.showerror("Git config",str(e),parent=self)
    def copy(self):self.clipboard_clear();self.clipboard_append(self.report);messagebox.showinfo("Git config","Copied report.",parent=self)
