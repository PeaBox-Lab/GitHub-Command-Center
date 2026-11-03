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

class CommitGraphWindow(tk.Toplevel):
    COLORS=("#60a5fa","#f472b6","#34d399","#fbbf24","#a78bfa","#22d3ee")
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Visual Commit History");self.geometry("1200x760")
        bar=ttk.Frame(self,padding=6);bar.pack(fill="x");ttk.Button(bar,text="Refresh",command=self.load).pack(side="left");ttk.Button(bar,text="Checkout selected",command=self.checkout).pack(side="left",padx=4)
        self.canvas=tk.Canvas(self,bg="#0b1220");ys=ttk.Scrollbar(self,orient="vertical",command=self.canvas.yview);self.canvas.configure(yscrollcommand=ys.set);ys.pack(side="right",fill="y");self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Button-1>",self.pick);self.selected=None;self.rows=[];self.load()
    def load(self):
        raw=git(self.repo,"log","--all","--topo-order","-250","--date=short","--pretty=format:%H%x1f%h%x1f%P%x1f%ad%x1f%an%x1f%s%x1f%D")
        self.data=[]
        for line in raw.splitlines():
            p=line.split("\x1f")
            if len(p)>=7:self.data.append(p)
        self.draw()
    def draw(self):
        c=self.canvas;c.delete("all");lanes={};next_lane=0;self.rows=[];rh=34
        for i,p in enumerate(self.data):
            full,short,parents,date,author,subject,refs=p;parents=parents.split()
            lane=lanes.pop(full,next_lane)
            if lane==next_lane:next_lane+=1
            if parents:lanes.setdefault(parents[0],lane)
            y=20+i*rh;x=24+lane*20;color=self.COLORS[lane%len(self.COLORS)]
            c.create_line(x,y-rh,x,y+rh,fill=color,width=2)
            for parent in parents[1:]:
                pl=lanes.setdefault(parent,next_lane)
                if pl==next_lane:next_lane+=1
                c.create_line(x,y,24+pl*20,y+rh,fill=self.COLORS[pl%len(self.COLORS)],width=2,smooth=True)
            c.create_oval(x-5,y-5,x+5,y+5,fill="#fbbf24" if self.selected==i else "white",outline=color,width=2)
            c.create_text(60+max(3,next_lane)*20,y,text=f"{short}  {subject}  {refs}  {author} · {date}",fill="#e2e8f0",anchor="w",font=("Consolas",9))
            self.rows.append((y-rh/2,y+rh/2,p))
        c.configure(scrollregion=(0,0,1800,max(100,len(self.data)*rh+40)))
    def pick(self,e):
        y=self.canvas.canvasy(e.y)
        for i,(a,b,p) in enumerate(self.rows):
            if a<=y<=b:self.selected=i;self.commit=p;self.draw();break
    def checkout(self):
        if self.selected is not None and messagebox.askyesno("Detached checkout",f"Checkout {self.commit[1]} in detached HEAD mode?",parent=self):
            try:git(self.repo,"switch","--detach",self.commit[0]);messagebox.showinfo("Checkout","Completed",parent=self)
            except Exception as e:messagebox.showerror("Checkout",str(e),parent=self)

class ConflictResolver(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Merge Conflict Resolver");self.geometry("1400x800")
        out=git(repo,"diff","--name-only","--diff-filter=U");self.files=[x for x in out.splitlines() if x and x!="Completed successfully."]
        if not self.files:self.after(50,lambda:(messagebox.showinfo("Conflicts","No unresolved conflicts.",parent=self),self.destroy()));return
        top=ttk.Frame(self,padding=6);top.pack(fill="x");self.file=tk.StringVar(value=self.files[0]);box=ttk.Combobox(top,textvariable=self.file,values=self.files,state="readonly",width=60);box.pack(side="left");box.bind("<<ComboboxSelected>>",lambda e:self.load())
        for t,c in [("Use ours",lambda:self.use("--ours")),("Use theirs",lambda:self.use("--theirs")),("Save",self.save),("Save + mark resolved",self.resolve),("Abort merge",self.abort)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=6,pady=6)
        self.ours=self.panel(pane,"OURS",False);self.merged=self.panel(pane,"MERGED RESULT",True);self.theirs=self.panel(pane,"THEIRS",False)
        for x in (self.ours,self.merged,self.theirs):pane.add(x[0],weight=1)
        self.load()
    def panel(self,parent,title,edit):
        f=ttk.Frame(parent);ttk.Label(f,text=title,font=("Segoe UI Semibold",10)).pack(anchor="w");t=tk.Text(f,wrap="none",undo=edit,font=("Consolas",9));t.pack(fill="both",expand=True)
        if not edit:t.config(state="disabled")
        return f,t
    def put(self,panel,value,lock=False):
        t=panel[1];t.config(state="normal");t.delete("1.0","end");t.insert("1.0",value)
        if lock:t.config(state="disabled")
    def version(self,n,p):
        try:return git(self.repo,"show",f":{n}:{p}")
        except:return "(unavailable)"
    def load(self):
        p=self.file.get();self.put(self.ours,self.version(2,p),True);self.put(self.theirs,self.version(3,p),True)
        try:v=(Path(self.repo)/p).read_text(encoding="utf-8",errors="replace")
        except:v=""
        self.put(self.merged,v)
    def use(self,side):
        if messagebox.askyesno("Replace",f"Use {side[2:]} version?",parent=self):git(self.repo,"checkout",side,"--",self.file.get());self.load()
    def save(self):(Path(self.repo)/self.file.get()).write_text(self.merged[1].get("1.0","end-1c"),encoding="utf-8")
    def resolve(self):
        self.save();git(self.repo,"add","--",self.file.get());self.files.remove(self.file.get())
        if not self.files:messagebox.showinfo("Resolved","All conflicts are staged. Commit to complete the merge.",parent=self);self.destroy()
        else:self.file.set(self.files[0]);self.load()
    def abort(self):
        if messagebox.askyesno("Abort merge","Abort the merge?",parent=self):git(self.repo,"merge","--abort");self.destroy()

class AdvancedGitWindow(tk.Toplevel):
    """Safe guided workflows for operations commonly hidden in Git context menus."""
    def __init__(self, parent, repo):
        super().__init__(parent)
        self.repo = repo
        self.title("Advanced Git Operations")
        self.geometry("980x700")
        self.minsize(850, 600)
        self._build()
        self.refresh()

    def _build(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(header, text=self.repo, font=("Segoe UI Semibold", 11)).pack(side="left", fill="x", expand=True)
        ttk.Button(header, text="Refresh", command=self.refresh).pack(side="right")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cherry = ttk.Frame(self.tabs, padding=10)
        self.rebase = ttk.Frame(self.tabs, padding=10)
        self.reset = ttk.Frame(self.tabs, padding=10)
        self.ignore = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.cherry, text="Cherry-pick")
        self.tabs.add(self.rebase, text="Rebase")
        self.tabs.add(self.reset, text="Reset & Revert")
        self.tabs.add(self.ignore, text=".gitignore")

        ttk.Label(self.cherry, text="Recent commits", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.commit_list = tk.Listbox(self.cherry, font=("Consolas", 9), height=18)
        self.commit_list.pack(fill="both", expand=True, pady=6)
        row = ttk.Frame(self.cherry); row.pack(fill="x")
        ttk.Button(row, text="Cherry-pick selected", command=self.cherry_pick).pack(side="left")
        ttk.Button(row, text="Abort cherry-pick", command=lambda:self.execute(["cherry-pick", "--abort"], confirm="Abort the current cherry-pick?" )).pack(side="left", padx=4)
        ttk.Button(row, text="Continue cherry-pick", command=lambda:self.execute(["cherry-pick", "--continue"])).pack(side="left")

        ttk.Label(self.rebase, text="Rebase the current branch onto another branch", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.branch_var = tk.StringVar()
        self.branch_box = ttk.Combobox(self.rebase, textvariable=self.branch_var, state="readonly")
        self.branch_box.pack(fill="x", pady=8)
        ttk.Label(self.rebase, text="A safety branch is created before rebase. Working tree must be clean.", foreground="#9a3412").pack(anchor="w", pady=(0, 10))
        rb = ttk.Frame(self.rebase); rb.pack(fill="x")
        ttk.Button(rb, text="Start safe rebase", command=self.start_rebase).pack(side="left")
        ttk.Button(rb, text="Continue", command=lambda:self.execute(["rebase", "--continue"])).pack(side="left", padx=4)
        ttk.Button(rb, text="Skip", command=lambda:self.execute(["rebase", "--skip"], confirm="Skip the current commit?" )).pack(side="left")
        ttk.Button(rb, text="Abort", command=lambda:self.execute(["rebase", "--abort"], confirm="Abort this rebase?" )).pack(side="left", padx=4)

        ttk.Label(self.reset, text="Revert creates a new undo commit and is the recommended shared-history option.", wraplength=800).pack(anchor="w", pady=(0, 8))
        self.hash_var = tk.StringVar()
        ttk.Entry(self.reset, textvariable=self.hash_var).pack(fill="x", pady=4)
        rr = ttk.Frame(self.reset); rr.pack(fill="x", pady=6)
        ttk.Button(rr, text="Revert commit", command=self.revert_commit).pack(side="left")
        ttk.Button(rr, text="Reset soft", command=lambda:self.reset_to("--soft")).pack(side="left", padx=4)
        ttk.Button(rr, text="Reset mixed", command=lambda:self.reset_to("--mixed")).pack(side="left")
        ttk.Button(rr, text="Reset hard", command=lambda:self.reset_to("--hard")).pack(side="left", padx=4)
        ttk.Label(self.reset, text="Hard reset permanently discards tracked working-tree and index changes. A backup branch is created first.", foreground="#b91c1c", wraplength=800).pack(anchor="w", pady=8)

        ttk.Label(self.ignore, text="Repository .gitignore editor", font=("Segoe UI Semibold", 11)).pack(anchor="w")
        self.ignore_text = tk.Text(self.ignore, wrap="none", undo=True, font=("Consolas", 10))
        self.ignore_text.pack(fill="both", expand=True, pady=6)
        ig = ttk.Frame(self.ignore); ig.pack(fill="x")
        ttk.Button(ig, text="Save .gitignore", command=self.save_ignore).pack(side="left")
        ttk.Button(ig, text="Add common Python rules", command=lambda:self.add_ignore("__pycache__/\n*.py[cod]\n.venv/\ndist/\nbuild/\n*.egg-info/\n.env\n")).pack(side="left", padx=4)
        ttk.Button(ig, text="Add common Node rules", command=lambda:self.add_ignore("node_modules/\ndist/\n.env\n*.log\ncoverage/\n")).pack(side="left")

    def refresh(self):
        try:
            commits = git(self.repo, "log", "--all", "-100", "--pretty=format:%H%x09%h%x09%s")
            self.commit_rows = []
            self.commit_list.delete(0, "end")
            for line in commits.splitlines():
                parts = line.split("\t", 2)
                if len(parts) == 3:
                    self.commit_rows.append(parts)
                    self.commit_list.insert("end", f"{parts[1]}  {parts[2]}")
            branch_text = git(self.repo, "branch", "--format=%(refname:short)")
            branches = [x for x in branch_text.splitlines() if x and x != "Completed successfully."]
            self.branch_box["values"] = branches
            if branches and not self.branch_var.get(): self.branch_var.set(branches[0])
            path = Path(self.repo) / ".gitignore"
            self.ignore_text.delete("1.0", "end")
            if path.exists(): self.ignore_text.insert("1.0", path.read_text(encoding="utf-8", errors="replace"))
        except Exception as exc:
            messagebox.showerror("Advanced Git", str(exc), parent=self)

    def execute(self, args, confirm=None):
        if confirm and not messagebox.askyesno("Confirm", confirm, parent=self): return
        try:
            out = git(self.repo, *args)
            messagebox.showinfo("Git", out, parent=self)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Git", str(exc), parent=self)

    def backup_branch(self, prefix):
        import datetime
        name = f"gccc-backup/{prefix}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        git(self.repo, "branch", name)
        return name

    def clean_required(self):
        state = git(self.repo, "status", "--porcelain")
        if state != "Completed successfully.":
            messagebox.showwarning("Clean working tree required", "Commit or stash changes before this operation.", parent=self)
            return False
        return True

    def cherry_pick(self):
        sel = self.commit_list.curselection()
        if not sel: return
        full, short, subject = self.commit_rows[sel[0]]
        if messagebox.askyesno("Cherry-pick", f"Apply {short} {subject} onto the current branch?", parent=self):
            self.execute(["cherry-pick", full])

    def start_rebase(self):
        target = self.branch_var.get()
        if not target or not self.clean_required(): return
        try:
            backup = self.backup_branch("pre-rebase")
            if not messagebox.askyesno("Safe rebase", f"Backup branch created:\n{backup}\n\nRebase current branch onto {target}?", parent=self): return
            self.execute(["rebase", target])
        except Exception as exc: messagebox.showerror("Rebase", str(exc), parent=self)

    def revert_commit(self):
        value = self.hash_var.get().strip()
        if value and messagebox.askyesno("Revert", f"Create a new commit reverting {value}?", parent=self): self.execute(["revert", "--no-edit", value])

    def reset_to(self, mode):
        value = self.hash_var.get().strip()
        if not value: return
        warning = f"Reset current branch to {value} using {mode}?"
        if mode == "--hard": warning += "\n\nTracked local changes will be permanently discarded."
        if not messagebox.askyesno("Reset", warning, parent=self): return
        try:
            backup = self.backup_branch("pre-reset")
            if messagebox.askyesno("Backup created", f"Created {backup}. Continue with reset?", parent=self): self.execute(["reset", mode, value])
        except Exception as exc: messagebox.showerror("Reset", str(exc), parent=self)

    def add_ignore(self, value):
        current = self.ignore_text.get("1.0", "end-1c")
        if current and not current.endswith("\n"): self.ignore_text.insert("end", "\n")
        self.ignore_text.insert("end", value)

    def save_ignore(self):
        try:
            (Path(self.repo) / ".gitignore").write_text(self.ignore_text.get("1.0", "end-1c") + "\n", encoding="utf-8")
            messagebox.showinfo(".gitignore", "Saved. Stage the file when ready.", parent=self)
        except Exception as exc: messagebox.showerror(".gitignore", str(exc), parent=self)

class RepositoryHealthCenter(tk.Toplevel):
    """Repository hygiene, documentation quality and maintenance dashboard."""
    def __init__(self, parent, repo):
        super().__init__(parent); self.repo=repo
        self.title("Repository Health Center"); self.geometry("1180x780"); self.minsize(950,650)
        self._build(); self.refresh()

    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        ttk.Label(top,text=self.repo,font=("Segoe UI Semibold",11)).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Refresh audit",command=self.refresh).pack(side="right")
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self.score_tab=ttk.Frame(self.tabs,padding=10);self.files_tab=ttk.Frame(self.tabs,padding=10);self.templates_tab=ttk.Frame(self.tabs,padding=10)
        self.tabs.add(self.score_tab,text="Health score");self.tabs.add(self.files_tab,text="Repository files");self.tabs.add(self.templates_tab,text="Templates")
        self.score=tk.Text(self.score_tab,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.score.pack(fill="both",expand=True)
        self.files=tk.Text(self.files_tab,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.files.pack(fill="both",expand=True)
        row=ttk.Frame(self.templates_tab);row.pack(fill="x",pady=(0,8))
        for title,fn in [("Create SECURITY.md",self.security_md),("Create CONTRIBUTING.md",self.contributing_md),("Create issue templates",self.issue_templates),("Create PR template",self.pr_template),("Create CODEOWNERS",self.codeowners),("Create .gitattributes",self.gitattributes)]:ttk.Button(row,text=title,command=fn).pack(side="left",padx=2,pady=2)
        self.template_info=tk.Text(self.templates_tab,wrap="word",font=("Segoe UI",10));self.template_info.pack(fill="both",expand=True)
        self.template_info.insert("1.0","Generate common repository-governance files directly into the working tree. Existing files are never overwritten without confirmation. Review and commit generated files through Local Git.")
        self.template_info.config(state="disabled")

    def present(self, rel): return (Path(self.repo)/rel).exists()
    def age_days(self, rel):
        p=Path(self.repo)/rel
        if not p.exists():return None
        import time
        return int((time.time()-p.stat().st_mtime)/86400)
    def refresh(self):
        checks=[]
        def add(label,points,maxp,detail):checks.append((label,points,maxp,detail))
        add("README.md",10 if self.present("README.md") else 0,10,"Present" if self.present("README.md") else "Missing")
        add("LICENSE",8 if self.present("LICENSE") else 0,8,"Present" if self.present("LICENSE") else "Missing")
        add("CHANGELOG.md",8 if self.present("CHANGELOG.md") else 0,8,"Present" if self.present("CHANGELOG.md") else "Missing")
        add("SECURITY.md",8 if self.present("SECURITY.md") else 0,8,"Present" if self.present("SECURITY.md") else "Missing")
        add("CONTRIBUTING.md",6 if self.present("CONTRIBUTING.md") else 0,6,"Present" if self.present("CONTRIBUTING.md") else "Missing")
        add("Pull request template",5 if self.present(".github/pull_request_template.md") else 0,5,"Present" if self.present(".github/pull_request_template.md") else "Missing")
        issue_dir=Path(self.repo)/".github"/"ISSUE_TEMPLATE";add("Issue templates",5 if issue_dir.exists() else 0,5,"Present" if issue_dir.exists() else "Missing")
        add("CODEOWNERS",5 if self.present(".github/CODEOWNERS") else 0,5,"Present" if self.present(".github/CODEOWNERS") else "Missing")
        add(".gitignore",5 if self.present(".gitignore") else 0,5,"Present" if self.present(".gitignore") else "Missing")
        add(".gitattributes",5 if self.present(".gitattributes") else 0,5,"Present" if self.present(".gitattributes") else "Missing")
        workflows=Path(self.repo)/".github"/"workflows";add("CI workflows",10 if workflows.exists() and list(workflows.glob("*.y*ml")) else 0,10,"Present" if workflows.exists() and list(workflows.glob("*.y*ml")) else "Missing")
        tests=any((Path(self.repo)/x).exists() for x in ("tests","test","pytest.ini","tox.ini"));add("Tests",10 if tests else 0,10,"Detected" if tests else "Not detected")
        try:
            tags=git(self.repo,"tag","--list");has_tag=tags!="Completed successfully.";add("Version tags",5 if has_tag else 0,5,"Present" if has_tag else "No tags")
        except:add("Version tags",0,5,"Unable to inspect")
        try:
            status=git(self.repo,"status","--porcelain");clean=status=="Completed successfully.";add("Clean working tree",5 if clean else 0,5,"Clean" if clean else "Uncommitted changes")
        except:add("Clean working tree",0,5,"Unable to inspect")
        total=sum(x[1] for x in checks);maximum=sum(x[2] for x in checks);pct=round(total/maximum*100) if maximum else 0
        rating="Excellent" if pct>=90 else "Good" if pct>=75 else "Needs attention" if pct>=55 else "High maintenance risk"
        text=f"REPOSITORY HEALTH SCORE: {pct}/100 - {rating}\n"+"="*78+"\n\n"
        for label,points,maxp,detail in checks:text+=f"[{points:>2}/{maxp:<2}] {label:<28} {detail}\n"
        text+="\nRecommended next actions:\n"
        for label,points,maxp,detail in checks:
            if points<maxp:text+=f"- Improve {label}: {detail}\n"
        self.score.delete("1.0","end");self.score.insert("1.0",text)
        self.refresh_files()
    def refresh_files(self):
        roots=["README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md","CODE_OF_CONDUCT.md",".gitignore",".gitattributes","pyproject.toml","requirements.txt","package.json","Dockerfile",".github/CODEOWNERS",".github/pull_request_template.md"]
        lines=[]
        for rel in roots:
            p=Path(self.repo)/rel
            if p.exists():lines.append(f"PRESENT  {rel:<38} {p.stat().st_size:>10} bytes")
            else:lines.append(f"MISSING  {rel}")
        gh=Path(self.repo)/".github"
        if gh.exists():
            lines.append("\n.github inventory:")
            for p in sorted(gh.rglob("*")):
                if p.is_file():lines.append("  "+str(p.relative_to(self.repo)))
        self.files.delete("1.0","end");self.files.insert("1.0","\n".join(lines))
    def write_template(self,rel,content):
        p=Path(self.repo)/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and not messagebox.askyesno("Replace file",f"{rel} already exists. Replace it?",parent=self):return
        p.write_text(content,encoding="utf-8");messagebox.showinfo("Created",f"Created {rel}. Review and commit it when ready.",parent=self);self.refresh()
    def security_md(self):self.write_template("SECURITY.md","# Security Policy\n\n## Reporting a vulnerability\n\nPlease report suspected vulnerabilities privately to the repository maintainers. Do not open a public issue for an unpatched vulnerability. Include affected versions, reproduction steps, impact, and any proposed remediation.\n\n## Supported versions\n\nThe latest stable release receives security fixes.\n")
    def contributing_md(self):self.write_template("CONTRIBUTING.md","# Contributing\n\n1. Create or link an issue.\n2. Create a focused branch.\n3. Add or update tests and documentation.\n4. Run relevant checks locally.\n5. Open a pull request with a clear summary, validation evidence, and risk notes.\n\nKeep changes small and avoid unrelated formatting changes.\n")
    def issue_templates(self):
        self.write_template(".github/ISSUE_TEMPLATE/bug_report.md","---\nname: Bug report\nabout: Report a reproducible problem\ntitle: '[Bug] '\nlabels: bug\n---\n\n## Description\n\n## Steps to reproduce\n1.\n\n## Expected behavior\n\n## Actual behavior\n\n## Environment\n- OS:\n- Version:\n\n## Logs/screenshots\n")
        self.write_template(".github/ISSUE_TEMPLATE/feature_request.md","---\nname: Feature request\nabout: Suggest an improvement\ntitle: '[Feature] '\nlabels: enhancement\n---\n\n## Problem\n\n## Proposed solution\n\n## Alternatives\n\n## Acceptance criteria\n- [ ]\n")
    def pr_template(self):self.write_template(".github/pull_request_template.md","## Summary\n\n## Changes\n- \n\n## Validation\n- [ ] Tests passed\n- [ ] Documentation updated\n- [ ] Security/release impact reviewed\n\n## Risk and rollback\n\n")
    def codeowners(self):
        owner=simpledialog.askstring("CODEOWNERS","GitHub owner/team, for example @username or @org/team:",parent=self)
        if owner:self.write_template(".github/CODEOWNERS",f"* {owner}\n")
    def gitattributes(self):self.write_template(".gitattributes","* text=auto eol=lf\n*.bat text eol=crlf\n*.cmd text eol=crlf\n*.png binary\n*.jpg binary\n*.jpeg binary\n*.gif binary\n*.zip binary\n*.pdf binary\n")
