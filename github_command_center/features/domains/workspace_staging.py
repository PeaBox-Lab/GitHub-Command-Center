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
