from __future__ import annotations
import json,tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox,ttk
from ...services.update_service import UpdateService

class UpdateCenter(tk.Toplevel):
    """User-confirmed, offline-verifiable update staging center."""
    def __init__(self,parent,repo=None,current_version="3.61.0"):
        super().__init__(parent);self.current=current_version;self.service=UpdateService();self.metadata_path=tk.StringVar();self.installer=tk.StringVar();self.title("Verified Update Center");self.geometry("940x650");self._build()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True)
        for row,(label,var,cmd) in enumerate((("Update metadata",self.metadata_path,self.choose_metadata),("Downloaded installer",self.installer,self.choose_installer))):
            ttk.Label(f,text=label).grid(row=row,column=0,sticky="w",pady=5);ttk.Entry(f,textvariable=var).grid(row=row,column=1,sticky="ew",padx=6);ttk.Button(f,text="Browse",command=cmd).grid(row=row,column=2)
        f.columnconfigure(1,weight=1);ttk.Button(f,text="Verify update",command=self.verify,style="Accent.TButton").grid(row=2,column=2,pady=8)
        self.out=tk.Text(f,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.grid(row=3,column=0,columnspan=3,sticky="nsew");f.rowconfigure(3,weight=1)
        ttk.Label(f,text="This center verifies metadata, version policy and SHA-256. It never silently installs or launches the installer.",padding=(0,8)).grid(row=4,column=0,columnspan=3,sticky="w")
    def choose_metadata(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("JSON","*.json"),("All files","*")]);self.metadata_path.set(p or self.metadata_path.get())
    def choose_installer(self):
        p=filedialog.askopenfilename(parent=self);self.installer.set(p or self.installer.get())
    def verify(self):
        try:
            m=self.service.load_metadata(self.metadata_path.get().strip());decision=self.service.is_allowed(self.current,m);hash_ok=self.service.verify(self.installer.get().strip(),m) if self.installer.get().strip() else False
            value=f"CURRENT VERSION: {self.current}\nCANDIDATE: {m.version}\nVERSION POLICY: {'PASS' if decision.allowed else 'BLOCK'}\nREASON: {decision.reason}\nINSTALLER SHA-256: {'PASS' if hash_ok else 'FAIL / NOT SELECTED'}\nNOTES: {m.notes_url}\nINSTALLER URL: {m.installer_url}\nSIGNATURE URL: {m.signature_url or '(not declared)'}\n\nInstallation remains user-controlled."
        except Exception as exc:value=str(exc)
        self.out.delete("1.0","end");self.out.insert("1.0",value)
