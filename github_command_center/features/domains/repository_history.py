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
