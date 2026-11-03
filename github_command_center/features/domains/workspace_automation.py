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

class HooksCenter(tk.Toplevel):
    """Manage repository-local Git hooks with templates and executable-bit handling."""
    TEMPLATES={
        "pre-commit":"#!/usr/bin/env sh\nset -e\ngit diff --cached --check\npython -m compileall -q .\n",
        "commit-msg":"#!/usr/bin/env sh\nmsg=$(head -n 1 \"$1\")\n[ ${#msg} -ge 8 ] || { echo 'Commit message must be at least 8 characters.'; exit 1; }\n",
        "pre-push":"#!/usr/bin/env sh\nset -e\npython -m compileall -q .\n",
    }
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.dir=Path(repo)/".git"/"hooks";self.title("Git Hooks Manager");self.geometry("1050x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.kind=tk.StringVar(value="pre-commit");ttk.Combobox(top,textvariable=self.kind,values=list(self.TEMPLATES),state="readonly",width=18).pack(side="left")
        for t,c in [("Load",self.load),("Use safe template",self.template),("Save & enable",self.save),("Disable",self.disable),("Test hook",self.test)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",undo=True,font=("Consolas",9));self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.status=tk.StringVar();ttk.Label(self,textvariable=self.status,padding=8).pack(fill="x")
    def path(self):return self.dir/self.kind.get()
    def refresh(self):self.status.set("Select a hook. Hooks are local to this clone and are not committed by default.");self.load()
    def load(self):
        p=self.path();self.text.delete("1.0","end")
        if p.exists():self.text.insert("1.0",p.read_text(encoding="utf-8"));self.status.set(f"Loaded {p.name}")
        else:self.status.set(f"{p.name} is not installed")
    def template(self):self.text.delete("1.0","end");self.text.insert("1.0",self.TEMPLATES[self.kind.get()])
    def save(self):
        p=self.path();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(self.text.get("1.0","end-1c")+"\n");p.chmod(p.stat().st_mode|0o111);self.status.set(f"Saved and enabled {p.name}")
    def disable(self):
        p=self.path()
        if p.exists():p.chmod(p.stat().st_mode&~0o111);self.status.set(f"Disabled {p.name}")
    def test(self):
        p=self.path()
        if not p.exists():return messagebox.showwarning("Hook","Save the hook first.",parent=self)
        try:
            r=run_process([str(p)],cwd=self.repo,timeout=120);messagebox.showinfo("Hook test",f"Exit code: {r.returncode}\n\n{r.stdout}\n{r.stderr}",parent=self)
        except Exception as e:messagebox.showerror("Hook test",str(e),parent=self)

class AutomationCenter(tk.Toplevel):
    """Extensible repository-local automation recipes stored as JSON."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-recipes.json";self.title("Automation Recipes");self.geometry("1100x720");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Run selected",self.run_selected),("Add recipe",self.add),("Delete",self.delete),("Reset defaults",self.defaults),("Save",self.save)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Segoe UI",10));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.describe())
        self.out=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
    def base(self):return [{"name":"Python syntax check","command":["python","-m","compileall","-q","."]},{"name":"Git integrity check","command":["git","fsck","--no-progress"]},{"name":"Whitespace check","command":["git","diff","--check"]}]
    def load(self):
        import json
        try:self.recipes=json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else self.base()
        except:self.recipes=self.base()
        self.render()
    def render(self):self.list.delete(0,"end");[self.list.insert("end",r["name"]) for r in self.recipes]
    def describe(self):
        s=self.list.curselection()
        if s:self.out.delete("1.0","end");self.out.insert("1.0","Command:\n"+" ".join(self.recipes[s[0]]["command"]))
    def add(self):
        import shlex
        n=simpledialog.askstring("Recipe","Recipe name:",parent=self);c=simpledialog.askstring("Recipe","Command line:",parent=self) if n else None
        if c:self.recipes.append({"name":n,"command":shlex.split(c)});self.render();self.save(False)
    def delete(self):
        s=self.list.curselection()
        if s:del self.recipes[s[0]];self.render();self.save(False)
    def defaults(self):self.recipes=self.base();self.render();self.save(False)
    def save(self,notice=True):
        import json
        self.path.write_text(json.dumps(self.recipes,indent=2))
        if notice:messagebox.showinfo("Recipes","Saved under .git/gccc-recipes.json",parent=self)
    def run_selected(self):
        s=self.list.curselection()
        if not s:return
        r=self.recipes[s[0]]
        try:
            p=run_process(r["command"],cwd=self.repo,timeout=900);v=f"Recipe: {r['name']}\nExit code: {p.returncode}\n\n{p.stdout}\n{p.stderr}"
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)

class IdentitySigningCenter(tk.Toplevel):
    """Configure repository identity and inspect commit/tag signature status."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Identity & Signing Center");self.geometry("1080x730");self._build();self.refresh()
    def _build(self):
        form=ttk.Frame(self,padding=8);form.pack(fill="x")
        self.name=tk.StringVar();self.email=tk.StringVar();self.key=tk.StringVar();self.sign=tk.BooleanVar()
        for i,(label,var) in enumerate((("User name",self.name),("User email",self.email),("Signing key",self.key))):
            ttk.Label(form,text=label).grid(row=i,column=0,sticky="w",pady=3);ttk.Entry(form,textvariable=var).grid(row=i,column=1,sticky="ew",padx=6,pady=3)
        form.columnconfigure(1,weight=1);ttk.Checkbutton(form,text="Sign commits by default in this repository",variable=self.sign).grid(row=3,column=1,sticky="w",pady=4)
        buttons=ttk.Frame(self,padding=(8,0));buttons.pack(fill="x")
        for t,c in [("Save repository identity",self.save),("Refresh",self.refresh),("List GPG keys",self.keys),("Verify recent commits",self.verify),("Create signed test tag",self.test_tag)]:ttk.Button(buttons,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=8)
    def cfg(self,key):
        try:v=git(self.repo,"config","--get",key);return "" if v=="Completed successfully." else v
        except:return ""
    def refresh(self):
        self.name.set(self.cfg("user.name"));self.email.set(self.cfg("user.email"));self.key.set(self.cfg("user.signingkey"));self.sign.set(self.cfg("commit.gpgsign").lower()=="true")
        self.out.delete("1.0","end");self.out.insert("1.0","Repository identity loaded. Repository-level settings override global Git identity only for this clone.\n\nSigning requires a configured GPG or SSH signing key supported by your Git installation.")
    def save(self):
        try:
            if self.name.get().strip():git(self.repo,"config","user.name",self.name.get().strip())
            if self.email.get().strip():git(self.repo,"config","user.email",self.email.get().strip())
            if self.key.get().strip():git(self.repo,"config","user.signingkey",self.key.get().strip())
            git(self.repo,"config","commit.gpgsign","true" if self.sign.get() else "false");messagebox.showinfo("Identity","Repository identity settings saved.",parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Identity",str(e),parent=self)
    def keys(self):
        try:
            r=run_process(["gpg","--list-secret-keys","--keyid-format=long"],timeout=60);v=(r.stdout+r.stderr).strip()
        except Exception as e:v="GPG unavailable: "+str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def verify(self):
        try:v=git(self.repo,"log","-30","--show-signature","--pretty=format:%h %ad %an %s","--date=short")
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def test_tag(self):
        import datetime
        tag="gccc-signing-test-"+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        if not messagebox.askyesno("Signed tag",f"Create local signed test tag {tag}? It will not be pushed.",parent=self):return
        try:messagebox.showinfo("Signed tag",git(self.repo,"tag","-s",tag,"-m","GitHub Command Center signing test"),parent=self)
        except Exception as e:messagebox.showerror("Signed tag",str(e),parent=self)

class CommitMessageStudio(tk.Toplevel):
    TYPES=("feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert")
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Commit Message Studio");self.geometry("980x720");self._build();self.update_preview()
    def _build(self):
        f=ttk.Frame(self,padding=10);f.pack(fill="x");self.typ=tk.StringVar(value="feat");self.scope=tk.StringVar();self.subject=tk.StringVar();self.breaking=tk.BooleanVar()
        ttk.Label(f,text="Type").grid(row=0,column=0,sticky="w");ttk.Combobox(f,textvariable=self.typ,values=self.TYPES,state="readonly",width=16).grid(row=0,column=1,sticky="w",padx=5)
        ttk.Label(f,text="Scope").grid(row=1,column=0,sticky="w");ttk.Entry(f,textvariable=self.scope).grid(row=1,column=1,sticky="ew",padx=5)
        ttk.Label(f,text="Subject").grid(row=2,column=0,sticky="w");ttk.Entry(f,textvariable=self.subject).grid(row=2,column=1,sticky="ew",padx=5)
        ttk.Checkbutton(f,text="Breaking change",variable=self.breaking,command=self.update_preview).grid(row=3,column=1,sticky="w");f.columnconfigure(1,weight=1)
        for var in (self.typ,self.scope,self.subject):var.trace_add("write",lambda *_:self.update_preview())
        ttk.Label(self,text="Body",padding=(10,4)).pack(anchor="w");self.body=tk.Text(self,height=8,wrap="word");self.body.pack(fill="x",padx=10);self.body.bind("<KeyRelease>",lambda e:self.update_preview())
        ttk.Label(self,text="Footer / issue references",padding=(10,4)).pack(anchor="w");self.footer=tk.Text(self,height=4,wrap="word");self.footer.pack(fill="x",padx=10);self.footer.bind("<KeyRelease>",lambda e:self.update_preview())
        self.preview=tk.Text(self,height=9,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.preview.pack(fill="both",expand=True,padx=10,pady=8)
        bar=ttk.Frame(self,padding=(10,0,10,10));bar.pack(fill="x");ttk.Button(bar,text="Copy message",command=self.copy).pack(side="left");ttk.Button(bar,text="Commit staged changes",command=self.commit).pack(side="right")
    def message(self):
        scope=f"({self.scope.get().strip()})" if self.scope.get().strip() else "";bang="!" if self.breaking.get() else "";head=f"{self.typ.get()}{scope}{bang}: {self.subject.get().strip()}"
        parts=[head];body=self.body.get("1.0","end-1c").strip();foot=self.footer.get("1.0","end-1c").strip()
        if body:parts.append(body)
        if self.breaking.get() and "BREAKING CHANGE:" not in foot:foot=(foot+"\n" if foot else "")+"BREAKING CHANGE: describe the incompatible behavior"
        if foot:parts.append(foot)
        return "\n\n".join(parts)
    def update_preview(self):
        self.preview.delete("1.0","end");self.preview.insert("1.0",self.message())
    def copy(self):self.clipboard_clear();self.clipboard_append(self.message());messagebox.showinfo("Commit message","Copied to clipboard.",parent=self)
    def commit(self):
        if not self.subject.get().strip():return messagebox.showwarning("Commit","Enter a subject.",parent=self)
        try:
            staged=git(self.repo,"diff","--cached","--name-only")
            if staged=="Completed successfully.":raise GitError("Nothing is staged.")
            if messagebox.askyesno("Commit",f"Commit staged changes with this message?\n\n{self.message()}",parent=self):messagebox.showinfo("Commit",git(self.repo,"commit","-m",self.message()),parent=self)
        except Exception as e:messagebox.showerror("Commit",str(e),parent=self)

class ChangelogStudio(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Changelog Studio");self.geometry("1080x740");self._build();self.generate()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.base=tk.StringVar();self.version=tk.StringVar(value="Unreleased")
        ttk.Label(top,text="Since ref").pack(side="left");ttk.Entry(top,textvariable=self.base,width=20).pack(side="left",padx=3);ttk.Label(top,text="Version").pack(side="left");ttk.Entry(top,textvariable=self.version,width=16).pack(side="left",padx=3)
        for t,c in [("Generate",self.generate),("Prepend to CHANGELOG",self.prepend),("Save section",self.save),("Copy",self.copy)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",undo=True,font=("Consolas",9));self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def generate(self):
        try:
            base=self.base.get().strip()
            if not base:
                try:base=git(self.repo,"describe","--tags","--abbrev=0");base="" if base=="Completed successfully." else base
                except:base=""
                self.base.set(base)
            args=["log","--pretty=format:%s%x1f%h"]+([f"{base}..HEAD"] if base else [])
            raw=git(self.repo,*args);groups={k:[] for k in ("Added","Fixed","Changed","Documentation","Tests","Build and CI","Other")}
            for line in raw.splitlines():
                if "\x1f" not in line:continue
                subject,h=line.split("\x1f",1);prefix=subject.split(":",1)[0].split("(",1)[0]
                group={"feat":"Added","fix":"Fixed","refactor":"Changed","perf":"Changed","docs":"Documentation","test":"Tests","build":"Build and CI","ci":"Build and CI"}.get(prefix,"Other")
                groups[group].append(f"- {subject} ({h})")
            section=f"## {self.version.get().strip() or 'Unreleased'}\n"
            for name,items in groups.items():
                if items:section+=f"\n### {name}\n"+"\n".join(items)+"\n"
            self.text.delete("1.0","end");self.text.insert("1.0",section)
        except Exception as e:messagebox.showerror("Changelog",str(e),parent=self)
    def prepend(self):
        p=Path(self.repo)/"CHANGELOG.md";section=self.text.get("1.0","end-1c").strip()+"\n\n";old=p.read_text(encoding="utf-8") if p.exists() else "# Changelog\n\n"
        if old.startswith("# Changelog"):new="# Changelog\n\n"+section+old[len("# Changelog"):].lstrip()
        else:new=section+old
        p.write_text(new);messagebox.showinfo("Changelog","CHANGELOG.md updated. Review and commit it.",parent=self)
    def save(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="changelog-section.md")
        if p:Path(p).write_text(self.text.get("1.0","end-1c")+"\n")
    def copy(self):self.clipboard_clear();self.clipboard_append(self.text.get("1.0","end-1c"));messagebox.showinfo("Changelog","Copied to clipboard.",parent=self)

class RemoteMigrationCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Remote Migration & Mirror Center");self.geometry("1000x690");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.name=tk.StringVar(value="backup");self.url=tk.StringVar();ttk.Entry(top,textvariable=self.name,width=15).pack(side="left");ttk.Entry(top,textvariable=self.url).pack(side="left",fill="x",expand=True,padx=4)
        for t,c in [("Add/update remote",self.set_remote),("Fetch all",self.fetch),("Push mirror",self.mirror),("Refresh",self.refresh)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Mirror push overwrites the destination refs to match this repository. Use only for a dedicated backup/migration remote and verify the URL carefully.",padding=8,foreground="#b91c1c").pack(fill="x")
    def refresh(self):
        try:v=git(self.repo,"remote","-v")+"\n\nREF SUMMARY\n"+git(self.repo,"show-ref")
        except Exception as e:v=str(e)
        self.text.delete("1.0","end");self.text.insert("1.0",v)
    def set_remote(self):
        n=self.name.get().strip();u=self.url.get().strip()
        if not n or not u:return
        try:
            existing=git(self.repo,"remote").splitlines();out=git(self.repo,"remote","set-url",n,u) if n in existing else git(self.repo,"remote","add",n,u);messagebox.showinfo("Remote",out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Remote",str(e),parent=self)
    def fetch(self):
        try:messagebox.showinfo("Fetch",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Fetch",str(e),parent=self)
    def mirror(self):
        n=self.name.get().strip()
        if n=="origin":return messagebox.showwarning("Mirror","Use a dedicated backup remote, not origin.",parent=self)
        if messagebox.askyesno("Mirror push",f"DANGEROUS: overwrite all refs on remote '{n}' to mirror this repository?",parent=self):
            confirm=simpledialog.askstring("Confirm mirror",f"Type the remote name exactly to continue: {n}",parent=self)
            if confirm==n:
                try:messagebox.showinfo("Mirror",git(self.repo,"push","--mirror",n),parent=self);self.refresh()
                except Exception as e:messagebox.showerror("Mirror",str(e),parent=self)

class CredentialAuditCenter(tk.Toplevel):
    """Inspect credential helpers and remote URL hygiene without exposing secrets."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Credential & Remote Hygiene");self.geometry("1050x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh audit",self.refresh),("Convert origin to SSH",self.to_ssh),("Convert origin to HTTPS",self.to_https),("Open GitHub auth status",self.gh_status)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        remote=self.safe("remote","-v");helpers=self.safe("config","--show-origin","--get-all","credential.helper")
        findings=[]
        for line in remote.splitlines():
            if "@" in line and "https://" in line:findings.append("WARN: HTTPS remote appears to contain embedded credentials or user information. Replace it immediately.")
            if "github.com" in line and not ("git@github.com:" in line or "https://github.com/" in line):findings.append("WARN: Non-standard GitHub remote format detected.")
        if not findings:findings.append("PASS: No obvious embedded credential pattern detected in remote URLs.")
        report="CREDENTIAL & REMOTE HYGIENE\n"+"="*72+"\n\nREMOTES\n"+remote+"\n\nCREDENTIAL HELPERS\n"+helpers+"\n\nFINDINGS\n"+"\n".join(findings)+"\n\nThis center never reads or displays stored passwords/tokens."
        self.text.delete("1.0","end");self.text.insert("1.0",report)
    def parse_origin(self):
        u=git(self.repo,"remote","get-url","origin")
        import re
        m=re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",u)
        if not m:raise GitError("Origin is not a recognizable GitHub URL.")
        return m.group(1),m.group(2)
    def to_ssh(self):
        try:
            owner,name=self.parse_origin();u=f"git@github.com:{owner}/{name}.git"
            if messagebox.askyesno("Remote URL",f"Set origin to SSH?\n{u}",parent=self):git(self.repo,"remote","set-url","origin",u);self.refresh()
        except Exception as e:messagebox.showerror("Remote URL",str(e),parent=self)
    def to_https(self):
        try:
            owner,name=self.parse_origin();u=f"https://github.com/{owner}/{name}.git"
            if messagebox.askyesno("Remote URL",f"Set origin to HTTPS?\n{u}",parent=self):git(self.repo,"remote","set-url","origin",u);self.refresh()
        except Exception as e:messagebox.showerror("Remote URL",str(e),parent=self)
    def gh_status(self):
        try:
            AsyncGitHubCenter(self,self.repo)
        except Exception as e:messagebox.showerror("GitHub authentication",str(e),parent=self)

class RepositoryMetricsCenter(tk.Toplevel):
    """Local engineering metrics without external analytics services."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Metrics Center");self.geometry("1100x740");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh metrics",command=self.refresh).pack(side="left");ttk.Button(top,text="Export report",command=self.export).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except:return ""
    def refresh(self):
        commits=self.safe("rev-list","--count","HEAD");contributors=self.safe("shortlog","-sne","HEAD");files=self.safe("ls-files").splitlines();languages={};total_lines=0
        extmap={".py":"Python",".js":"JavaScript",".ts":"TypeScript",".tsx":"TypeScript",".java":"Java",".go":"Go",".rs":"Rust",".md":"Markdown",".html":"HTML",".css":"CSS",".sh":"Shell"}
        for f in files:
            p=Path(self.repo)/f;lang=extmap.get(p.suffix.lower())
            if lang:
                try:n=len(p.read_text(encoding="utf-8",errors="ignore").splitlines());languages[lang]=languages.get(lang,0)+n;total_lines+=n
                except:pass
        monthly=self.safe("log","--date=format:%Y-%m","--pretty=format:%ad");counts={}
        for m in monthly.splitlines():counts[m]=counts.get(m,0)+1
        report=f"REPOSITORY METRICS\n{'='*72}\nCommits: {commits}\nTracked files: {len(files)}\nCounted text lines: {total_lines}\n\nCONTRIBUTORS\n{contributors or 'Unavailable'}\n\nLANGUAGE LINES (heuristic)\n"
        for k,v in sorted(languages.items(),key=lambda x:-x[1]):report+=f"{k:<18}{v:>10}\n"
        report+="\nCOMMITS BY MONTH\n"
        for k,v in sorted(counts.items(),reverse=True)[:24]:report+=f"{k}: {v}\n"
        self.report=report;self.text.delete("1.0","end");self.text.insert("1.0",report)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile=Path(self.repo).name+"-metrics.txt")
        if p:Path(p).write_text(self.report)
