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
from ...core.process_gateway import run_process, start_process

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
        if p:Path(p).write_text(self.report)

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
        if p:Path(p).write_text(self.report)

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
        r=run_process(["git","show",f":{stage}:{path}"],cwd=self.repo,timeout=120,binary=True)
        return r.stdout.decode("utf-8") if r.returncode==0 else "(stage unavailable or binary)"
    def load(self):
        p=self.selected()
        if not p:return
        values={"BASE stage 1":self.blob(1,p),"OURS stage 2":self.blob(2,p),"THEIRS stage 3":self.blob(3,p)}
        try:values["WORKTREE"]=(Path(self.repo)/p).read_text(encoding="utf-8")
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
        if p:Path(p).write_text(self.report)

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
        if p:Path(p).write_text(self.raw)

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
        if p:Path(p).write_text(self.report)

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
