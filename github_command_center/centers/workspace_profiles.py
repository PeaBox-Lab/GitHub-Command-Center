"""Workspace Profile Center: save and reopen common repository contexts."""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from ..services.workspace_profile_service import WorkspaceProfile, WorkspaceProfileService
from ..core.command_gateway import git
from ..core.error_boundary import HANDLED_EXCEPTIONS

class WorkspaceProfileCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.service=WorkspaceProfileService();self.title("Workspace Profiles");self.geometry("860x540");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=10);top.pack(fill="x")
        ttk.Label(top,text="Saved Workspaces",font=("Segoe UI Semibold",14)).pack(side="left")
        for text,cmd in [("Save current",self.save_current),("Open",self.open_selected),("Delete",self.delete_selected),("Export",self.export_profiles),("Import",self.import_profiles)]: ttk.Button(top,text=text,command=cmd).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("name","repo","branch","note"),show="headings",height=16)
        for c,t,w in [("name","Name",150),("repo","Repository",330),("branch","Branch",140),("note","Note",180)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=10,pady=(0,10));self.tree.bind("<Double-1>",lambda e:self.open_selected())
    def refresh(self):
        self.tree.delete(*self.tree.get_children());self.rows=self.service.load()
        for i,p in enumerate(self.rows): self.tree.insert("","end",iid=str(i),values=(p.name,p.repository,p.branch,p.note))
    def selected(self):
        sel=self.tree.selection(); return self.rows[int(sel[0])] if sel else None
    def save_current(self):
        name=simpledialog.askstring("Workspace profile","Profile name",parent=self); 
        if not name:return
        try: branch=git(self.repo,"branch","--show-current")
        except HANDLED_EXCEPTIONS: branch=""
        note=simpledialog.askstring("Workspace profile","Optional note",parent=self) or ""
        self.service.upsert(WorkspaceProfile(name,str(Path(self.repo).resolve()),branch.strip(),note));self.refresh()
    def open_selected(self):
        p=self.selected()
        if not p:return
        path=Path(p.repository)
        if not path.exists():messagebox.showerror("Workspace Profiles",f"Repository no longer exists:\n{path}",parent=self);return
        if p.branch:
            try:git(path,"switch",p.branch)
            except HANDLED_EXCEPTIONS as e:messagebox.showwarning("Workspace Profiles",f"Opened repository, but branch switch failed:\n{e}",parent=self)
        LocalGitWindow(self,path)
    def delete_selected(self):
        p=self.selected()
        if p and messagebox.askyesno("Workspace Profiles",f"Delete profile '{p.name}'?",parent=self):self.service.remove(p.name);self.refresh()
    def export_profiles(self):
        target=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile="github-command-center-workspaces.json")
        if target:self.service.export_to(target)
    def import_profiles(self):
        source=filedialog.askopenfilename(parent=self,filetypes=[("JSON","*.json"),("All files","*.*")])
        if not source:return
        try:self.service.import_from(source);self.refresh()
        except (OSError,ValueError,KeyError,TypeError) as e:messagebox.showerror("Workspace Profiles",str(e),parent=self)
