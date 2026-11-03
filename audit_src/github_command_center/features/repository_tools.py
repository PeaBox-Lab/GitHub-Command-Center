"""GitHub Command Center feature windows.

Extracted in v3.73 to keep the application shell independently maintainable.
"""
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.command_gateway import GitError, git

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
