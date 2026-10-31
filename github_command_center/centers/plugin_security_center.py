from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ..services.plugin_security import PluginSecurityService
from ..services.plugin_trust import PluginTrustStore


class PluginSecurityCenter(tk.Toplevel):
    """Audit plugin manifests, permissions, executables, hashes, and publisher trust."""

    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.service = PluginSecurityService()
        self.trust = PluginTrustStore()
        self.manifest_path = tk.StringVar()
        self.package_path = tk.StringVar()
        self.require_signature = tk.BooleanVar()
        self.title("Plugin Security Center")
        self.geometry("1120x760")
        self._build()
        self.refresh_trust()

    def _build(self):
        top = ttk.Frame(self, padding=8);top.pack(fill="x")
        ttk.Entry(top, textvariable=self.manifest_path).pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="Manifest", command=self.choose_manifest).pack(side="left", padx=3)
        ttk.Entry(top, textvariable=self.package_path, width=34).pack(side="left")
        ttk.Button(top, text="Package/executable", command=self.choose_package).pack(side="left", padx=3)
        ttk.Button(top, text="Audit", command=self.audit, style="Accent.TButton").pack(side="left")
        trust_bar = ttk.Frame(self, padding=(8,0));trust_bar.pack(fill="x")
        self.publisher = tk.StringVar();ttk.Entry(trust_bar, textvariable=self.publisher).pack(side="left", fill="x", expand=True)
        ttk.Button(trust_bar, text="Trust publisher", command=self.trust_publisher).pack(side="left", padx=3)
        ttk.Button(trust_bar, text="Remove trust", command=self.untrust_publisher).pack(side="left")
        ttk.Checkbutton(trust_bar, text="Require signatures", variable=self.require_signature, command=self.save_policy).pack(side="left", padx=8)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);left=ttk.Frame(pane);right=ttk.Frame(pane);pane.add(left,weight=2);pane.add(right,weight=3)
        ttk.Label(left,text="Trusted publishers",font=("Segoe UI Semibold",10)).pack(anchor="w");self.publishers=tk.Listbox(left,font=("Consolas",9));self.publishers.pack(fill="both",expand=True)
        self.out=tk.Text(right,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="Audit does not execute the plugin. Trust is explicit and local. HMAC support is for local verification/test workflows; public distribution should use certificate-backed signatures in a future release.",padding=8).pack(fill="x")

    def choose_manifest(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Plugin manifest","*.json"),("All files","*")])
        if p:self.manifest_path.set(p);self.audit()
    def choose_package(self):
        p=filedialog.askopenfilename(parent=self)
        if p:self.package_path.set(p)
    def refresh_trust(self):
        value=self.trust.load();self.require_signature.set(value["require_signature"]);self.publishers.delete(0,"end")
        for p in value["publishers"]:self.publishers.insert("end",p)
    def save_policy(self):
        value=self.trust.load();self.trust.save(value["publishers"],self.require_signature.get())
    def trust_publisher(self):
        p=self.publisher.get().strip()
        if not p:return
        value=self.trust.load();self.trust.save([*value["publishers"],p],self.require_signature.get());self.refresh_trust()
    def untrust_publisher(self):
        p=self.publisher.get().strip();value=self.trust.load();self.trust.save([x for x in value["publishers"] if x!=p],self.require_signature.get());self.refresh_trust()
    def audit(self):
        try:
            manifest=self.service.load(self.manifest_path.get().strip());policy=self.trust.load();result=self.service.assess(manifest,trusted_publishers=policy["publishers"],require_signature=policy["require_signature"])
            lines=["PLUGIN SECURITY AUDIT","="*72,f"ID: {manifest.plugin_id}",f"Name: {manifest.name}",f"Version: {manifest.version}",f"Publisher: {manifest.publisher or '(none)'}",f"Executable: {manifest.command[0] if manifest.command else '(none)'}",f"Permissions: {', '.join(manifest.permissions) or '(none)'}",f"Decision: {'ALLOW' if result.allowed else 'BLOCK'}"]
            if self.package_path.get().strip() and manifest.sha256:
                lines.append(f"SHA-256 verification: {'PASS' if self.service.verify_file(self.package_path.get().strip(),manifest.sha256) else 'FAIL'}")
            lines += ["","ERRORS",*(result.errors or ["None"]),"","WARNINGS",*(result.warnings or ["None"]),"","CANONICAL PAYLOAD",manifest.canonical_payload().decode("utf-8")]
            value="\n".join(lines)
        except Exception as exc:value=str(exc)
        self.out.delete("1.0","end");self.out.insert("1.0",value)
