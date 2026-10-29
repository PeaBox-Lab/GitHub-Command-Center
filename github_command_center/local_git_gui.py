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
        for t,c in [("Diff",self.diff),("Discard",self.discard),("Clean preview",self.clean),("Open folder",self.open_folder)]:ttk.Button(foot,text=t,command=c).pack(side="left",padx=2)
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
