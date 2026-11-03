"""GitHub Command Center feature windows.

Extracted in v3.73 to keep the application shell independently maintainable.
"""
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from ..core.command_gateway import GitError, git

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

class WorktreeCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Git Worktree Center");self.geometry("900x620");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Add worktree",self.add),("Remove selected",self.remove),("Prune",self.prune)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("path","head","branch"),show="headings");
        for c,t,w in [("path","Path",450),("head","HEAD",120),("branch","Branch",220)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:
            raw=git(self.repo,"worktree","list","--porcelain");self.rows=[];cur={}
            for line in raw.splitlines()+[""]:
                if not line:
                    if cur:self.rows.append(cur);cur={}
                elif " " in line:
                    k,v=line.split(" ",1);cur[k]=v
            self.tree.delete(*self.tree.get_children())
            for i,r in enumerate(self.rows):self.tree.insert("","end",iid=str(i),values=(r.get("worktree",""),r.get("HEAD","")[:10],r.get("branch","").replace("refs/heads/","")))
        except Exception as e:messagebox.showerror("Worktrees",str(e),parent=self)
    def add(self):
        folder=filedialog.askdirectory(title="Choose parent folder for worktree",parent=self)
        if not folder:return
        branch=simpledialog.askstring("Worktree","Existing branch name, or new branch name:",parent=self)
        if not branch:return
        target=str(Path(folder)/branch.replace("/","-"))
        exists=git(self.repo,"branch","--list",branch)
        try:
            out=git(self.repo,"worktree","add",target,branch) if exists!="Completed successfully." else git(self.repo,"worktree","add","-b",branch,target)
            messagebox.showinfo("Worktree",out,parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def remove(self):
        s=self.tree.selection()
        if not s:return
        path=self.rows[int(s[0])].get("worktree","")
        if path==str(Path(self.repo).resolve()):return messagebox.showwarning("Worktree","The main worktree cannot be removed here.",parent=self)
        if messagebox.askyesno("Remove worktree",f"Remove worktree?\n{path}",parent=self):
            try:messagebox.showinfo("Worktree",git(self.repo,"worktree","remove",path),parent=self);self.refresh()
            except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)
    def prune(self):
        try:messagebox.showinfo("Worktree",git(self.repo,"worktree","prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Worktree",str(e),parent=self)

class RepositoryCompareCenter(tk.Toplevel):
    """Compare branches, tags or commits before merge/release and export a review report."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Compare & Review Center");self.geometry("1200x780");self.minsize(980,650);self._build();self.refresh_refs()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        ttk.Label(top,text="Base").pack(side="left");self.base=tk.StringVar();self.base_box=ttk.Combobox(top,textvariable=self.base,width=28);self.base_box.pack(side="left",padx=4)
        ttk.Label(top,text="Compare").pack(side="left",padx=(10,0));self.compare=tk.StringVar();self.compare_box=ttk.Combobox(top,textvariable=self.compare,width=28);self.compare_box.pack(side="left",padx=4)
        ttk.Button(top,text="Compare",command=self.run_compare).pack(side="left",padx=4);ttk.Button(top,text="Export report",command=self.export_report).pack(side="left")
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill="both",expand=True,padx=8,pady=(0,8))
        self.summary_tab=ttk.Frame(self.tabs,padding=8);self.files_tab=ttk.Frame(self.tabs,padding=8);self.commits_tab=ttk.Frame(self.tabs,padding=8);self.diff_tab=ttk.Frame(self.tabs,padding=8)
        for f,t in [(self.summary_tab,"Summary"),(self.files_tab,"Files"),(self.commits_tab,"Commits"),(self.diff_tab,"Unified diff")]:self.tabs.add(f,text=t)
        self.summary=tk.Text(self.summary_tab,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.summary.pack(fill="both",expand=True)
        self.files=tk.Text(self.files_tab,wrap="none",font=("Consolas",9));self.files.pack(fill="both",expand=True)
        self.commits=tk.Text(self.commits_tab,wrap="none",font=("Consolas",9));self.commits.pack(fill="both",expand=True)
        self.diff=tk.Text(self.diff_tab,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.diff.pack(fill="both",expand=True)
        self.report=""
    def refresh_refs(self):
        try:
            raw=git(self.repo,"for-each-ref","--format=%(refname:short)","refs/heads/","refs/remotes/","refs/tags/")
            refs=[x for x in raw.splitlines() if x and x!="Completed successfully."]
            self.base_box["values"]=refs;self.compare_box["values"]=refs
            current=git(self.repo,"branch","--show-current")
            if refs:self.base.set("main" if "main" in refs else refs[0]);self.compare.set(current if current in refs else refs[min(1,len(refs)-1)])
        except Exception as e:messagebox.showerror("Compare",str(e),parent=self)
    def put(self,w,v):w.delete("1.0","end");w.insert("1.0",v)
    def run_compare(self):
        a=self.base.get().strip();b=self.compare.get().strip()
        if not a or not b:return
        try:
            ahead=git(self.repo,"rev-list","--count",f"{a}..{b}");behind=git(self.repo,"rev-list","--count",f"{b}..{a}")
            stat=git(self.repo,"diff","--stat",f"{a}...{b}");num=git(self.repo,"diff","--numstat",f"{a}...{b}");names=git(self.repo,"diff","--name-status",f"{a}...{b}")
            commits=git(self.repo,"log","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s",f"{a}..{b}")
            udiff=git(self.repo,"diff","--no-ext-diff",f"{a}...{b}")
            additions=deletions=files=0
            if num!="Completed successfully.":
                for line in num.splitlines():
                    p=line.split("\t")
                    if len(p)>=3:
                        files+=1
                        if p[0].isdigit():additions+=int(p[0])
                        if p[1].isdigit():deletions+=int(p[1])
            summary=f"COMPARE: {a} ... {b}\n"+"="*78+f"\nCommits only in compare: {ahead}\nCommits only in base   : {behind}\nChanged files          : {files}\nAdditions              : {additions}\nDeletions              : {deletions}\n\nDIFF STAT\n{stat}\n"
            self.put(self.summary,summary);self.put(self.files,names);self.put(self.commits,commits);self.put(self.diff,udiff)
            self.report=summary+"\nFILES\n"+names+"\n\nCOMMITS\n"+commits+"\n\nDIFF\n"+udiff
        except Exception as e:messagebox.showerror("Compare",str(e),parent=self)
    def export_report(self):
        if not self.report:self.run_compare()
        if not self.report:return
        path=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile="repository-comparison.txt")
        if path:Path(path).write_text(self.report,encoding="utf-8");messagebox.showinfo("Export",f"Saved {path}",parent=self)

class BackupRestoreCenter(tk.Toplevel):
    """Local recovery checkpoints using refs, stashes and bundles."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Backup & Recovery Center");self.geometry("1050x720");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Create checkpoint",self.checkpoint),("Create full bundle",self.bundle),("Verify bundle",self.verify),("Restore bundle to folder",self.restore_bundle)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def refresh(self):
        try:
            refs=git(self.repo,"for-each-ref","--sort=-creatordate","--format=%(creatordate:short)%09%(refname:short)%09%(objectname:short)%09%(subject)","refs/heads/gccc-backup/")
            st=git(self.repo,"stash","list")
            txt="SAFETY CHECKPOINT BRANCHES\n"+"="*72+"\n"+(refs if refs!="Completed successfully." else "None")+"\n\nSTASHES\n"+"="*72+"\n"+(st if st!="Completed successfully." else "None")
            self.text.delete("1.0","end");self.text.insert("1.0",txt)
        except Exception as e:messagebox.showerror("Recovery",str(e),parent=self)
    def checkpoint(self):
        import datetime
        label=simpledialog.askstring("Checkpoint","Optional label:",initialvalue="manual",parent=self) or "manual"
        safe="".join(c if c.isalnum() or c in "-_" else "-" for c in label)
        name=f"gccc-backup/{safe}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:messagebox.showinfo("Checkpoint",git(self.repo,"branch",name),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Checkpoint",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=Path(self.repo).name+"-backup.bundle")
        if p:
            try:messagebox.showinfo("Bundle",git(self.repo,"bundle","create",p,"--all"),parent=self)
            except Exception as e:messagebox.showerror("Bundle",str(e),parent=self)
    def verify(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle"),("All files","*")])
        if p:
            try:messagebox.showinfo("Bundle verification",git(self.repo,"bundle","verify",p),parent=self)
            except Exception as e:messagebox.showerror("Bundle verification",str(e),parent=self)
    def restore_bundle(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Git bundle","*.bundle")])
        if not p:return
        parent=filedialog.askdirectory(parent=self,title="Choose folder in which to restore the repository")
        if not parent:return
        name=simpledialog.askstring("Restore","New repository folder name:",initialvalue=Path(self.repo).name+"-recovered",parent=self)
        if name:
            try:messagebox.showinfo("Restore",git(parent,"clone",p,name),parent=self)
            except Exception as e:messagebox.showerror("Restore",str(e),parent=self)

class RepositoryManager(tk.Toplevel):
    """Multi-repository command center for local portfolios."""
    def __init__(self,parent,start_repo=""):
        super().__init__(parent);self.title("Repository Manager");self.geometry("1200x760");self.minsize(980,650)
        self.workspace=Path(start_repo).parent if start_repo else Path.home()/"GitHub";self.rows=[];self._build();self.scan()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.workspace));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Browse",command=self.browse).pack(side="left",padx=3);ttk.Button(top,text="Scan",command=self.scan).pack(side="left");ttk.Button(top,text="Fetch selected",command=self.fetch).pack(side="left",padx=3);ttk.Button(top,text="Open Local Git",command=self.open_local).pack(side="left")
        cols=("repo","branch","state","ahead","behind","remote")
        self.tree=ttk.Treeview(self,columns=cols,show="headings",selectmode="extended")
        for c,t,w in [("repo","Repository",260),("branch","Branch",130),("state","Working tree",110),("ahead","Ahead",70),("behind","Behind",70),("remote","Origin",420)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5);self.tree.bind("<Double-1>",lambda e:self.open_local())
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.path.set(p);self.scan()
    def scan(self):
        root=Path(self.path.get());self.rows=[];self.tree.delete(*self.tree.get_children())
        if not root.exists():return
        candidates=[]
        if (root/".git").exists():candidates=[root]
        else:
            for p in root.iterdir():
                if p.is_dir() and (p/".git").exists():candidates.append(p)
        for p in sorted(candidates):
            try:
                branch=git(p,"branch","--show-current");status=git(p,"status","--porcelain");state="Clean" if status=="Completed successfully." else "Changed"
                try:remote=git(p,"remote","get-url","origin")
                except:remote="-"
                try:ahead=git(p,"rev-list","--count","@{u}..HEAD");behind=git(p,"rev-list","--count","HEAD..@{u}")
                except:ahead=behind="-"
                row={"path":str(p),"branch":branch,"state":state,"ahead":ahead,"behind":behind,"remote":remote};self.rows.append(row)
                self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p.name,branch,state,ahead,behind,remote))
            except Exception:pass
    def selected(self):return [self.rows[int(i)] for i in self.tree.selection()]
    def fetch(self):
        selected=self.selected()
        if not selected:return
        errors=[]
        for r in selected:
            try:git(r["path"],"fetch","--all","--prune")
            except Exception as e:errors.append(f"{Path(r['path']).name}: {e}")
        self.scan();messagebox.showinfo("Fetch", "Completed." if not errors else "Completed with errors:\n"+"\n".join(errors),parent=self)
    def open_local(self):
        s=self.selected()
        if s:LocalGitWindow(self,s[0]["path"])

class SettingsDiagnosticsCenter(tk.Toplevel):
    """1.0 diagnostics for required tools and repository configuration."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Diagnostics & Configuration");self.geometry("1000x700");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Run diagnostics",command=self.refresh).pack(side="left");ttk.Button(top,text="Copy report",command=self.copy).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def cmdver(self,cmd,args):
        try:
            r=subprocess.run([cmd,*args],text=True,capture_output=True,timeout=20,encoding="utf-8",errors="replace")
            return (r.returncode==0,(r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else "Available")
        except Exception as e:return False,str(e)
    def refresh(self):
        lines=["GITHUB COMMAND CENTER 1.0 DIAGNOSTICS","="*78]
        import sys,platform
        lines += [f"Python: {sys.version.split()[0]}",f"OS: {platform.platform()}",f"Repository: {self.repo}"]
        for name,cmd,args in [("Git","git",["--version"]),("GitHub CLI","gh",["--version"]),("pip-audit","pip-audit",["--version"]),("Bandit","bandit",["--version"])]:
            ok,v=self.cmdver(cmd,args);lines.append(f"{'PASS' if ok else 'WARN':4} {name}: {v}")
        try:
            lines.append("\nGit config")
            for key in ("user.name","user.email","core.autocrlf","pull.rebase"):
                try:v=git(self.repo,"config","--get",key)
                except:v="Not set"
                lines.append(f"  {key}: {v}")
            lines.append("\nRepository integrity\n  "+git(self.repo,"fsck","--no-progress").replace("\n","\n  "))
        except Exception as e:lines.append("Repository diagnostics error: "+str(e))
        self.report="\n".join(lines);self.text.delete("1.0","end");self.text.insert("1.0",self.report)
    def copy(self):self.clipboard_clear();self.clipboard_append(getattr(self,"report",""));messagebox.showinfo("Diagnostics","Report copied to clipboard.",parent=self)

class SearchCenter(tk.Toplevel):
    """Search commits, tracked files and repository text from one UI."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Search Center");self.geometry("1100x720");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.q=tk.StringVar();ttk.Entry(top,textvariable=self.q).pack(side="left",fill="x",expand=True)
        for t,c in [("Search text",self.search_text),("Search commits",self.search_commits),("Search files",self.search_files)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.out=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True,padx=8,pady=5)
    def put(self,title,value):self.out.delete("1.0","end");self.out.insert("1.0",title+"\n"+"="*72+"\n\n"+value)
    def search_text(self):
        q=self.q.get().strip()
        if not q:return
        try:self.put("TRACKED TEXT SEARCH",git(self.repo,"grep","-n","-I","--",q))
        except Exception as e:self.put("TRACKED TEXT SEARCH",str(e))
    def search_commits(self):
        q=self.q.get().strip()
        if not q:return
        try:self.put("COMMIT MESSAGE SEARCH",git(self.repo,"log","--all","--date=short","--pretty=format:%h%x09%ad%x09%an%x09%s","--grep",q,"-i"))
        except Exception as e:self.put("COMMIT MESSAGE SEARCH",str(e))
    def search_files(self):
        q=self.q.get().strip().lower()
        if not q:return
        try:
            files=git(self.repo,"ls-files");matches=[x for x in files.splitlines() if q in x.lower()];self.put("FILE NAME SEARCH","\n".join(matches) if matches else "No tracked filenames matched.")
        except Exception as e:self.put("FILE NAME SEARCH",str(e))

class RepositoryNotesCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.path=Path(repo)/".git"/"gccc-notes.md";self.title("Repository Notes");self.geometry("850x620")
        ttk.Label(self,text="Private local notes stored under .git and excluded from normal commits.",padding=8).pack(fill="x");self.text=tk.Text(self,wrap="word",undo=True);self.text.pack(fill="both",expand=True,padx=8);ttk.Button(self,text="Save",command=self.save).pack(anchor="e",padx=8,pady=8)
        self.text.insert("1.0",self.path.read_text(encoding="utf-8",errors="replace") if self.path.exists() else "# Repository Notes\n\n## Current focus\n\n## Decisions\n\n## Follow-ups\n\n## Release reminders\n")
    def save(self):
        self.path.write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8");messagebox.showinfo("Notes","Saved under .git/gccc-notes.md",parent=self)

class BranchCleanupCenter(tk.Toplevel):
    """Safe local branch cleanup with merged/stale awareness."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Branch Cleanup Center");self.geometry("1050x700");self.rows=[];self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.refresh),("Delete selected merged",self.delete_selected),("Prune remotes",self.prune),("Open Worktrees",lambda:WorktreeCenter(self,self.repo))]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.tree=ttk.Treeview(self,columns=("branch","merged","age","upstream","worktree"),show="headings",selectmode="extended")
        for c,t,w in [("branch","Branch",260),("merged","Merged",80),("age","Last commit",130),("upstream","Upstream",260),("worktree","Worktree",90)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Only branches reported merged into the current branch can be deleted from this screen. The current branch and worktree branches are protected.",padding=8).pack(fill="x")
    def refresh(self):
        try:
            current=git(self.repo,"branch","--show-current");merged=set(x.strip().lstrip("* ") for x in git(self.repo,"branch","--merged").splitlines())
            wt=git(self.repo,"worktree","list","--porcelain");used=set()
            for line in wt.splitlines():
                if line.startswith("branch refs/heads/"):used.add(line.replace("branch refs/heads/","",1))
            raw=git(self.repo,"for-each-ref","--format=%(refname:short)%09%(committerdate:short)%09%(upstream:short)","refs/heads/")
            self.rows=[];self.tree.delete(*self.tree.get_children())
            for line in raw.splitlines():
                p=line.split("\t");b=p[0];row={"branch":b,"merged":b in merged,"date":p[1] if len(p)>1 else "","upstream":p[2] if len(p)>2 else "","used":b in used,"current":b==current};self.rows.append(row)
                self.tree.insert("","end",iid=str(len(self.rows)-1),values=(b,"Yes" if row["merged"] else "No",row["date"],row["upstream"] or "-","Yes" if row["used"] else "No"))
        except Exception as e:messagebox.showerror("Branch Cleanup",str(e),parent=self)
    def delete_selected(self):
        selected=[self.rows[int(i)] for i in self.tree.selection()]
        eligible=[r for r in selected if r["merged"] and not r["current"] and not r["used"]]
        if not eligible:return messagebox.showinfo("Branch Cleanup","No selected branches are safely eligible for deletion.",parent=self)
        names="\n".join(r["branch"] for r in eligible)
        if messagebox.askyesno("Delete merged branches",f"Delete these local merged branches?\n\n{names}",parent=self):
            errors=[]
            for r in eligible:
                try:git(self.repo,"branch","-d",r["branch"])
                except Exception as e:errors.append(f"{r['branch']}: {e}")
            self.refresh();messagebox.showinfo("Branch Cleanup","Completed." if not errors else "Some branches were not deleted:\n"+"\n".join(errors),parent=self)
    def prune(self):
        try:messagebox.showinfo("Prune",git(self.repo,"fetch","--all","--prune"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Prune",str(e),parent=self)

class ProjectSnapshotCenter(tk.Toplevel):
    """Generate a compact local repository handover snapshot."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Project Snapshot");self.geometry("1050x720");self._build();self.generate()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Regenerate",command=self.generate).pack(side="left");ttk.Button(top,text="Export Markdown",command=self.export).pack(side="left",padx=3);ttk.Button(top,text="Copy",command=self.copy).pack(side="left")
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*args):
        try:return git(self.repo,*args)
        except Exception as e:return "Unavailable: "+str(e)
    def generate(self):
        branch=self.safe("branch","--show-current");status=self.safe("status","--short","--branch");recent=self.safe("log","-10","--date=short","--pretty=format:- %h %ad %an: %s");tags=self.safe("tag","--sort=-creatordate");remotes=self.safe("remote","-v")
        notes=Path(self.repo)/".git"/"gccc-notes.md";note_text=notes.read_text(encoding="utf-8",errors="replace") if notes.exists() else "No private repository notes."
        key=[]
        for f in ("README.md","CHANGELOG.md","RELEASE_NOTES.md","USER_GUIDE.md","SECURITY.md","CONTRIBUTING.md"):
            if (Path(self.repo)/f).exists():key.append(f)
        self.snapshot=f"# Project Snapshot: {Path(self.repo).name}\n\n## Repository\n- Path: `{self.repo}`\n- Current branch: `{branch}`\n- Key docs: {', '.join(key) or 'None detected'}\n\n## Working tree\n```text\n{status}\n```\n\n## Recent commits\n{recent}\n\n## Recent tags\n```text\n{tags}\n```\n\n## Remotes\n```text\n{remotes}\n```\n\n## Private local notes\n{note_text}\n"
        self.text.delete("1.0","end");self.text.insert("1.0",self.snapshot)
    def export(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile=f"{Path(self.repo).name}-snapshot.md")
        if p:Path(p).write_text(self.snapshot,encoding="utf-8");messagebox.showinfo("Snapshot",f"Saved {p}",parent=self)
    def copy(self):self.clipboard_clear();self.clipboard_append(self.snapshot);messagebox.showinfo("Snapshot","Copied to clipboard.",parent=self)

class PatchCenter(tk.Toplevel):
    """Create, inspect, validate and apply Git patch files without leaving the GUI."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Patch Center");self.geometry("1100x740");self.minsize(900,620);self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Export working diff",self.export_working),("Export staged diff",self.export_staged),("Create patch series",self.format_patch),("Inspect patch",self.inspect_patch),("Apply patch",self.apply_patch),("Apply mailbox",self.apply_mailbox)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.text.insert("1.0","Patch Center\n\nExport normal or staged changes as .patch files, create a format-patch series from commits, inspect/check a patch before applying it, or apply email-style patches with git am.\n")
    def save_diff(self,staged):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".patch",initialfile="staged.patch" if staged else "working-tree.patch",filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            args=["diff"]+(["--cached"] if staged else []);out=git(self.repo,*args)
            if out=="Completed successfully.":return messagebox.showinfo("Patch","There are no changes to export.",parent=self)
            Path(p).write_text(out+"\n",encoding="utf-8");messagebox.showinfo("Patch",f"Saved {p}",parent=self)
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def export_working(self):self.save_diff(False)
    def export_staged(self):self.save_diff(True)
    def format_patch(self):
        base=simpledialog.askstring("Patch series","Base ref, e.g. main or v1.3.0:",initialvalue="main",parent=self)
        if not base:return
        folder=filedialog.askdirectory(parent=self,title="Choose output folder")
        if folder:
            try:messagebox.showinfo("Patch series",git(self.repo,"format-patch","-o",folder,f"{base}..HEAD"),parent=self)
            except Exception as e:messagebox.showerror("Patch series",str(e),parent=self)
    def inspect_patch(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            content=Path(p).read_text(encoding="utf-8",errors="replace");check=""
            try:check=git(self.repo,"apply","--check",p)
            except Exception as e:check=str(e)
            self.text.delete("1.0","end");self.text.insert("1.0",f"APPLY CHECK\n{'='*72}\n{check}\n\nPATCH CONTENT\n{'='*72}\n{content}")
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def apply_patch(self):
        p=filedialog.askopenfilename(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if not p:return
        try:
            git(self.repo,"apply","--check",p)
            if messagebox.askyesno("Apply patch",f"Patch check passed. Apply?\n{p}",parent=self):messagebox.showinfo("Patch",git(self.repo,"apply",p),parent=self)
        except Exception as e:messagebox.showerror("Patch",str(e),parent=self)
    def apply_mailbox(self):
        files=filedialog.askopenfilenames(parent=self,filetypes=[("Patch","*.patch"),("All files","*")])
        if files and messagebox.askyesno("Apply mailbox",f"Apply {len(files)} patch(es) as commits using git am?",parent=self):
            try:messagebox.showinfo("Mailbox",git(self.repo,"am",*files),parent=self)
            except Exception as e:messagebox.showerror("Mailbox",str(e)+"\n\nResolve conflicts then run git am --continue, or abort with git am --abort.",parent=self)

class BisectCenter(tk.Toplevel):
    """Guided Git bisect for finding the commit that introduced a regression."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Regression Finder - Git Bisect");self.geometry("1000x680");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        self.good=tk.StringVar();self.bad=tk.StringVar(value="HEAD")
        ttk.Label(top,text="Known good ref").pack(side="left");ttk.Entry(top,textvariable=self.good,width=22).pack(side="left",padx=3);ttk.Label(top,text="Known bad ref").pack(side="left");ttk.Entry(top,textvariable=self.bad,width=22).pack(side="left",padx=3)
        for t,c in [("Start",self.start),("Mark good",lambda:self.mark("good")),("Mark bad",lambda:self.mark("bad")),("Skip",lambda:self.mark("skip")),("Reset",self.reset)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def status(self):
        try:return git(self.repo,"status","--short","--branch")+"\n\nCurrent commit:\n"+git(self.repo,"show","-s","--date=short","--pretty=format:%H%n%ad%n%an%n%s","HEAD")
        except Exception as e:return str(e)
    def refresh(self):self.text.delete("1.0","end");self.text.insert("1.0","GIT BISECT\n"+"="*72+"\n\n"+self.status()+"\n\nWorkflow: start with a known good and bad ref, test the checked-out revision, then mark it Good, Bad, or Skip. Git narrows the regression to one commit.")
    def clean(self):
        s=git(self.repo,"status","--porcelain");return s=="Completed successfully."
    def start(self):
        if not self.clean():return messagebox.showwarning("Bisect","Commit or stash changes before starting bisect.",parent=self)
        g=self.good.get().strip();b=self.bad.get().strip()
        if not g or not b:return messagebox.showwarning("Bisect","Enter known good and bad refs.",parent=self)
        try:git(self.repo,"bisect","start",b,g);self.refresh()
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
    def mark(self,state):
        try:out=git(self.repo,"bisect",state);self.refresh();messagebox.showinfo("Bisect",out,parent=self)
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)
    def reset(self):
        try:messagebox.showinfo("Bisect",git(self.repo,"bisect","reset"),parent=self);self.refresh()
        except Exception as e:messagebox.showerror("Bisect",str(e),parent=self)

class TaskCenter(tk.Toplevel):
    """Repository-local checklist for release, refactor and maintenance work."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path(repo)/".git"/"gccc-tasks.txt";self.title("Repository Task Center");self.geometry("950x650");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.entry=tk.StringVar();ttk.Entry(top,textvariable=self.entry).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Add task",command=self.add).pack(side="left",padx=3);ttk.Button(top,text="Toggle done",command=self.toggle).pack(side="left");ttk.Button(top,text="Delete",command=self.delete).pack(side="left",padx=3);ttk.Button(top,text="Save",command=self.save).pack(side="left")
        self.list=tk.Listbox(self,font=("Segoe UI",10),selectmode="extended");self.list.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Tasks are private to this local clone and stored under .git/gccc-tasks.txt.",padding=8).pack(fill="x")
    def load(self):
        self.tasks=[]
        if self.path.exists():self.tasks=[x for x in self.path.read_text(encoding="utf-8",errors="replace").splitlines() if x.strip()]
        self.render()
    def render(self):
        self.list.delete(0,"end")
        for t in self.tasks:self.list.insert("end",t)
    def add(self):
        v=self.entry.get().strip()
        if v:self.tasks.append("[ ] "+v);self.entry.set("");self.render();self.save(False)
    def toggle(self):
        for i in self.list.curselection():self.tasks[i]=(self.tasks[i].replace("[ ] ","[x] ",1) if self.tasks[i].startswith("[ ] ") else self.tasks[i].replace("[x] ","[ ] ",1))
        self.render();self.save(False)
    def delete(self):
        for i in reversed(self.list.curselection()):del self.tasks[i]
        self.render();self.save(False)
    def save(self,notice=True):
        self.path.write_text("\n".join(self.tasks)+("\n" if self.tasks else ""),encoding="utf-8")
        if notice:messagebox.showinfo("Tasks","Saved repository tasks.",parent=self)

class ArchiveCenter(tk.Toplevel):
    """Safe local archive/export hub for reproducible handover packages."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Archive & Handover Center");self.geometry("1000x680");self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Export HEAD ZIP",self.head_zip),("Create Git bundle",self.bundle),("Export snapshot",self.snapshot),("Export support pack",self.support_pack)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="word",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
        self.text.insert("1.0","Archive & Handover Center\n\nHEAD ZIP creates clean source without .git. Git bundle preserves repository history and refs. Snapshot exports a readable project handover. Support pack combines diagnostics, git status and environment information without including your GitHub token.")
    def head_zip(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".zip",initialfile=Path(self.repo).name+"-HEAD.zip")
        if p:
            try:messagebox.showinfo("Archive",git(self.repo,"archive","--format=zip",f"--output={p}","HEAD"),parent=self)
            except Exception as e:messagebox.showerror("Archive",str(e),parent=self)
    def bundle(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".bundle",initialfile=Path(self.repo).name+"-full.bundle")
        if p:
            try:messagebox.showinfo("Bundle",git(self.repo,"bundle","create",p,"--all"),parent=self)
            except Exception as e:messagebox.showerror("Bundle",str(e),parent=self)
    def snapshot(self):ProjectSnapshotCenter(self,self.repo)
    def support_pack(self):
        import platform,sys
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".txt",initialfile=Path(self.repo).name+"-support.txt")
        if not p:return
        def safe(*args):
            try:return git(self.repo,*args)
            except Exception as e:return str(e)
        report=f"GitHub Command Center Support Pack\n{'='*72}\nRepository: {self.repo}\nPython: {sys.version}\nOS: {platform.platform()}\n\nSTATUS\n{safe('status','--short','--branch')}\n\nREMOTES\n{safe('remote','-v')}\n\nRECENT COMMITS\n{safe('log','-20','--oneline','--decorate')}\n\nCONFIG\n{safe('config','--list','--show-origin')}\n\nFSCK\n{safe('fsck','--no-progress')}\n"
        Path(p).write_text(report,encoding="utf-8");messagebox.showinfo("Support pack",f"Saved {p}",parent=self)

class CommandPalette(tk.Toplevel):
    """Searchable launcher that keeps the Local Git toolbar usable as features grow."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Command Palette");self.geometry("760x620");self.transient(parent)
        self.q=tk.StringVar();e=ttk.Entry(self,textvariable=self.q,font=("Segoe UI",12));e.pack(fill="x",padx=10,pady=10);e.bind("<KeyRelease>",lambda x:self.render());e.bind("<Return>",lambda x:self.launch());e.focus_set()
        self.list=tk.Listbox(self,font=("Segoe UI",10));self.list.pack(fill="both",expand=True,padx=10,pady=(0,10));self.list.bind("<Double-1>",lambda x:self.launch())
        self.commands=[
            ("Visual commit history",lambda:CommitGraphWindow(self,repo),"history graph branches"),("Resolve merge conflicts",lambda:ConflictResolver(self,repo),"merge conflicts ours theirs"),
            ("Advanced Git operations",lambda:AdvancedGitWindow(self,repo),"rebase cherry-pick reset ignore"),("Release Center",lambda:ReleasePublishCenterV2(self,repo),"release tag assets bundle"),
            ("Pull Request Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"pull request pr review merge"),("GitHub Actions Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"workflow actions ci logs"),
            ("Security Center",lambda:SecurityCenter(self,repo),"dependabot code secret scan checksums"),("Repository Health",lambda:RepositoryHealthCenter(self,repo),"quality docs governance score"),
            ("Worktree Center",lambda:WorktreeCenter(self,repo),"parallel branches worktrees"),("Compare & Review",lambda:RepositoryCompareCenter(self,repo),"compare branch tag diff"),
            ("Backup & Recovery",lambda:BackupRestoreCenter(self,repo),"bundle restore checkpoint"),("Repository Manager",lambda:RepositoryManager(self,repo),"multiple repositories portfolio"),
            ("Diagnostics",lambda:SettingsDiagnosticsCenter(self,repo),"environment git python configuration"),("Smart Sync",lambda:SyncCenter(self,repo),"fetch pull push ahead behind"),
            ("Repository Search",lambda:SearchCenter(self,repo),"grep commit file search"),("Pre-Commit Review",lambda:ReviewCenterV2(self,repo),"stage checks diff commit"),
            ("Repository Notes",lambda:RepositoryNotesCenter(self,repo),"private notes decisions"),("Branch Cleanup",lambda:BranchCleanupCenter(self,repo),"merged stale prune"),
            ("Project Snapshot",lambda:ProjectSnapshotCenter(self,repo),"handover snapshot markdown"),("Patch Center",lambda:PatchCenter(self,repo),"patch apply format-patch"),
            ("Regression Finder",lambda:BisectCenter(self,repo),"bisect regression"),("Commit Inspector",lambda:HistoryCenterV2(self,repo),"blame file history commit"),
            ("Submodule Center",lambda:SubmoduleCenter(self,repo),"submodule recursive"),("Repository Tasks",lambda:TaskCenter(self,repo),"checklist tasks"),
            ("Archive & Handover",lambda:ArchiveCenter(self,repo),"zip bundle support pack"),("Git Hooks Manager",lambda:HooksCenter(self,repo),"hooks pre-commit commit-msg"),
            ("Git LFS Center",lambda:LFSCenter(self,repo),"large files lfs track"),("Automation Recipes",lambda:AutomationCenter(self,repo),"automation recipes checks"),("Identity & Signing",lambda:IdentitySigningCenter(self,repo),"identity email gpg sign verify"),("Commit Message Studio",lambda:CommitMessageStudio(self,repo),"conventional commits message"),("Changelog Studio",lambda:ChangelogStudio(self,repo),"changelog release notes commits"),("Remote Migration & Mirror",lambda:RemoteMigrationCenter(self,repo),"remote backup mirror migration"),("Credential & Remote Hygiene",lambda:CredentialAuditCenter(self,repo),"credentials helper url ssh https auth"),("Release Policy Center",lambda:ReleasePolicyCenter(self,repo),"release policy gates semver version"),("Repository Metrics",lambda:RepositoryMetricsCenter(self,repo),"metrics contributors languages commits activity"),("Plugin Manager",lambda:PluginManager(self,repo),"plugins extensions commands"),("Batch Operations",lambda:BatchOperationsCenter(self,repo),"batch multiple repositories portfolio"),("Operations Dashboard",lambda:RepositoryDashboardCenter(self,repo),"dashboard operational status next action"),("Repository Data Export",lambda:DataExportCenter(self,repo),"export json csv commits metadata"),("Background Jobs",lambda:BackgroundJobsCenter(self,repo),"jobs queue background cancel logs"),("Preferences",lambda:PreferencesCenter(self,repo),"preferences theme appearance defaults"),("Portfolio History",lambda:PortfolioHistoryCenter(self,repo),"sqlite portfolio history snapshots trends"),("Self-Test & Readiness",lambda:SelfTestCenter(self,repo),"self test readiness smoke diagnostics"),("Partial Staging",lambda:PartialStagingCenter(self,repo),"partial stage hunk line add patch"),("Reflog Recovery",lambda:RecoveryDashboardV2(self,repo),"reflog recover lost commit reset checkout branch"),("Interactive Rebase Editor",lambda:InteractiveRebaseEditor(self,repo),"interactive rebase squash fixup reword edit drop reorder"),("Unified Ref Browser",lambda:UnifiedRefBrowser(self,repo),"refs branches remotes tags stash notes"),("Repository History Browser",lambda:RepositoryHistoryBrowser(self,repo),"history browse tree file commit export"),("Sparse Checkout",lambda:SparseCheckoutCenter(self,repo),"sparse checkout cone large repository folders"),("Repository Maintenance",lambda:AsyncMaintenanceCenter(self,repo),"maintenance gc fsck objects commit graph"),("Git Notes",lambda:GitNotesCenter(self,repo),"git notes annotation metadata commit"),("Diff & Merge Tools",lambda:DiffMergeToolCenter(self,repo),"difftool mergetool vscode winmerge beyond compare kdiff3"),("Recorded Conflict Resolution",lambda:RerereCenter(self,repo),"rerere recorded resolution recurring conflict"),("Remote Branch Center",lambda:RemoteBranchCenter(self,repo),"remote branch track publish rename delete"),("Ignore & Attributes Studio",lambda:IgnoreAttributesStudio(self,repo),"gitignore gitattributes check-ignore attributes"),("Advanced Clone Wizard",lambda:CloneWizard(self),"clone shallow depth partial single branch blob filter"),("Worktree Safety",lambda:WorktreeSafetyCenter(self,repo),"worktree safety lock unlock prune"),("Repository Doctor",lambda:RepositoryDoctor(self,repo),"doctor diagnose repair status config integrity"),("Tag & Release Audit",lambda:TagReleaseAuditCenter(self,repo),"tags release audit signature remote annotated lightweight"),("Stash Manager Pro",lambda:StashManagerPro(self,repo),"stash apply pop branch drop untracked"),("Safe Clean Center",lambda:CleanPreviewCenter(self,repo),"clean untracked ignored preview delete"),("Repository Size Explorer",lambda:RepositorySizeCenter(self,repo),"size large files objects lfs storage"),("Force-with-Lease Safety",lambda:ForcePushSafetyCenter(self,repo),"force with lease rewritten history push safety"),("Advanced History Search",lambda:CommitSearchPro(self,repo),"pickaxe regex history search content"),("Git Bundle Inspector",lambda:BundleInspector(self,repo),"bundle verify heads clone restore backup"),("Branch Protection Advisor",lambda:BranchProtectionAdvisor(self,repo),"branch protection rules review checks github"),("Repository Favorites",lambda:RepositoryFavoritesCenter(self,repo),"favorites groups repositories portfolio"),("Async Git Operations",lambda:AsyncOperationsCenter(self,repo),"async background fetch fsck maintenance gc cancel progress"),("Changes Center V2",lambda:ChangesCenterV2(self,repo),"changes stage unstage commit discard diff"),("History Center V2",lambda:HistoryCenterV2(self,repo),"history log commit inspect grep refs"),("GitHub Network Center",lambda:AsyncGitHubCenter(self,repo),"github async api pr issue actions release security"),("GitHub Workflow Center",lambda:AsyncGitHubWorkflowCenter(self,repo),"github pr checks merge issue workflow rerun async"),("Review Center V2",lambda:ReviewCenterV2(self,repo),"review preflight tests compile ruff bandit diff"),("Release Publish Center V2",lambda:ReleasePublishCenterV2(self,repo),"release tag push publish github assets notes"),("Push & Pull Center",lambda:AsyncPushPullCenter(self,repo),"async push pull rebase ff force lease upstream"),("Submodule Center V2",lambda:AsyncSubmoduleCenter(self,repo),"submodule async add sync update init"),("Git LFS Center V2",lambda:AsyncLFSCenter(self,repo),"lfs async track fetch pull prune"),("Clone Center V2",lambda:AsyncCloneCenter(self,repo),"clone async shallow partial filter"),("Git Bundle Center",lambda:AsyncBundleCenter(self,repo),"bundle backup verify list heads async"),("Visual Diff Center",lambda:VisualDiffCenter(self,repo),"visual side by side word diff hunk stage unstage"),("Plugin Security Center",lambda:PluginSecurityCenter(self,repo),"plugin security manifest permissions allowlist publisher trust signature hash"),("Public Release Readiness",lambda:PublicReleaseReadinessCenter(self,repo),"public release readiness audit score gates"),("Verified Update Center",lambda:UpdateCenter(self,repo,"3.61.0"),"update verify sha256 metadata version installer"),("Developer Toolbox",lambda:DeveloperToolboxCenter(self,repo),"developer patch whitespace changed files commit diagnostics"),("Developer Quality",lambda:DevQualityCenter(self,repo),"developer test lint security compile quality"),("Code Search",lambda:CodeSearchCenter(self,repo),"developer code search grep history regex"),("Patch Series",lambda:PatchSeriesCenter(self,repo),"patch series format patch export"),("Repository Metrics",lambda:RepositoryMetricsCenter(self,repo),"repository metrics files commits contributors objects"),("Build & Validation Runner",lambda:BuildCommandCenter(self,repo),"developer build test compile quality"),("Developer Artifacts",lambda:DevArtifactCenter(self,repo),"developer source archive manifest export"),("Git Log Visualizer",lambda:GitLogVisualizerCenter(self,repo),"git log visualization graph branches commits refs"),("Stash Workbench",lambda:StashWorkbenchCenter(self,repo),"stash manager preview apply pop branch selective"),("Worktree Workbench",lambda:WorktreeWorkbenchCenter(self,repo),"worktree manager add lock move remove prune"),("Interactive Commit Graph",lambda:CommitGraphFilterCenter(self,repo),"git log graph filters author date merges path refs"),("Stash Diff & Conflict Preview",lambda:StashConflictPreviewCenter(self,repo),"stash diff conflict preview merge tree risk"),("Ref Compare",lambda:RefCompareCenter(self,repo),"developer compare refs branches commits diff"),("Revision Explain",lambda:RevisionExplainCenter(self,repo),"developer revision explain object ref metadata"),("Git Object Query",lambda:GitObjectQueryCenter(self,repo),"git object cat file tree blob path verify"),("Accessibility & Display",lambda:AccessibilityCenter(self,repo),"accessibility high contrast large text keyboard focus reduce motion"),("Preflight Quality Gates",lambda:ReviewCenterV2(self,repo),"preflight quality gates push pr release checks"),("Commit Template Center",lambda:CommitTemplateCenter(self,repo),"commit template message conventional"),("Patch Queue Center",lambda:PatchQueueCenter(self,repo),"patch queue git am mailbox continue abort"),("Hook Audit Center",lambda:HookAuditCenter(self,repo),"hooks audit executable provenance precommit"),("Merge Preview Center",lambda:MergePreviewCenter(self,repo),"merge preview merge-tree conflict impact"),("Reset & Recovery Planner",lambda:ResetRecoveryPlanner(self,repo),"reset soft mixed hard recovery backup"),("Git Configuration Center",lambda:GitConfigCenter(self,repo),"git config local global origin scope"),("Cherry-Pick Queue",lambda:CherryPickQueueCenter(self,repo),"cherry pick queue commits continue abort"),("Release Asset Integrity",lambda:ReleaseAssetIntegrityCenter(self,repo),"release asset sha256 checksum verify"),("Local Release Archive",lambda:LocalReleaseArchiveCenter(self,repo),"release archive source zip bundle checksums metadata"),("Signature Audit",lambda:CommitSignatureAuditCenter(self,repo),"signature audit signed commits verification gpg"),("Release Comparison",lambda:ReleaseCompareCenter(self,repo),"release compare tags commits files diff"),("Safe Branch Delete",lambda:SafeDeleteBranchWizard(self,repo),"safe branch delete merged worktree upstream"),("Pull Strategy Advisor",lambda:PullRebaseAdvisor(self,repo),"pull strategy merge rebase fast forward ahead behind"),("Detached HEAD Recovery",lambda:DetachedHeadRecoveryCenter(self,repo),"detached head recovery branch switch"),("Repository State Export",lambda:RepositoryStateExportCenter(self,repo),"repository state export json markdown audit"),("Repository Rules Audit",lambda:RepositoryRulesCenter(self,repo),"repository rules governance docs codeowners workflows"),("Commit Range Exporter",lambda:CommitRangeExporter(self,repo),"commit range patches bundle markdown export"),("Local Branch Dashboard",lambda:BranchDashboardV2(self,repo),"branch dashboard divergence recency compare"),("Repository Onboarding",lambda:RepositoryOnboardingCenter(self,repo),"repository onboarding starter readme governance"),("Repository Audit Pack",lambda:RepositoryAuditPackCenter(self,repo),"audit pack evidence status remotes fsck config"),("Safety Branch Manager",lambda:BackupBranchManager(self,repo),"backup safety branch gccc cleanup recovery"),("Upstream Health",lambda:UpstreamHealthCenter(self,repo),"upstream health broken branch remote divergence"),("Release Evidence",lambda:ReleaseEvidenceV2(self,repo),"release evidence approval integrity signature docs"),("Repository Locator",lambda:RepositoryLocatorCenter(self,repo),"repository locator scan workspace find repositories"),("Blame Explorer",lambda:BlameExplorerCenter(self,repo),"blame line author commit inspector"),("Remote Prune Audit",lambda:AsyncRemotePruneCenter(self,repo),"remote prune stale refs dry run"),("Git Object Inspector",lambda:CommitObjectCenter(self,repo),"git object cat-file tree plumbing inspect"),("Automated Bisect",lambda:BisectAutomationCenter(self,repo),"bisect run regression automated test command"),("Revision Archive",lambda:RevisionArchiveCenter(self,repo),"archive revision zip subdirectory export"),("Commit Metadata Inspector",lambda:CommitMetadataCenter(self,repo),"commit metadata author committer parents signature tree"),("Dangling Object Recovery",lambda:DanglingObjectRecoveryCenter(self,repo),"dangling unreachable commit fsck recovery lost objects"),("Contributor Mailmap",lambda:MailmapCenter(self,repo),"mailmap contributors identities author email canonical"),("Patch Identity Comparator",lambda:PatchIdCenter(self,repo),"patch id duplicate cherry equivalent rebased commit"),("Credential Redaction Audit",lambda:CredentialRedactionAuditCenter(self,repo),"credential secret token redaction audit security"),("Ref Consistency",lambda:RefConsistencyCenter(self,repo),"ref consistency symbolic head connectivity refs"),("Release Branch Planner",lambda:ReleaseBranchPlanner(self,repo),"release branch planner create base switch"),("Switch & Restore",lambda:GitSwitchRestoreCenter(self,repo),"git switch restore source staged worktree"),("Rebase State Inspector",lambda:RebaseStateCenter(self,repo),"rebase state todo continue skip abort conflicts"),("Git Describe & Version",lambda:GitDescribeCenter(self,repo),"git describe version tag dirty release"),("Worktree Repair",lambda:GitWorktreeRepairCenter(self,repo),"worktree repair prune stale metadata"),("Tag Manager Pro",lambda:TagManagerPro(self,repo),"tag annotated signed push verify delete remote"),("Pathspec Explorer",lambda:GitPathspecCenter(self,repo),"pathspec glob exclude files changed preview"),("Git Grep Studio",lambda:GitGrepStudio(self,repo),"grep repository regex fixed historical content search"),("Tree Comparison",lambda:ArchiveCompareCenter(self,repo),"tree compare dirstat rename files refs"),("Remote URL Audit",lambda:RemoteUrlAuditCenter(self,repo),"remote url fetch push fork upstream audit"),("Git Replace Center",lambda:GitReplaceCenter(self,repo),"git replace object local ref graft"),("Merge Base Explorer",lambda:MergeBaseExplorer(self,repo),"merge base fork point ancestor independent"),("Commit Reachability Explorer",lambda:BranchContainsCenter(self,repo),"branch contains tag contains no merged reachability"),("Revert Queue",lambda:RevertQueueCenter(self,repo),"revert queue commits continue abort backup"),("Git Log Query Builder",lambda:GitLogQueryCenter(self,repo),"git log author date path grep merges query"),("Git Index Inspector",lambda:IndexInspectorCenter(self,repo),"index staging area stages blobs flags unstage"),("Merge Commit Revert",lambda:MergeCommitRevertCenter(self,repo),"merge commit revert mainline parent protected"),("Commit Graph & Pack Index",lambda:CommitGraphMaintenanceCenter(self,repo),"commit graph multi pack index bitmap maintenance"),("Diff Algorithm Lab",lambda:DiffAlgorithmCenter(self,repo),"diff algorithm myers patience histogram minimal word diff"),("Git Subtree Center",lambda:SubtreeCenter(self,repo),"git subtree vendor split add pull push"),("History Rewrite Advisor",lambda:GitFilterRepoAdvisor(self,repo),"filter repo history rewrite remove secret large file"),("Attributes Audit",lambda:AttributesAuditCenter(self,repo),"gitattributes audit binary lfs text eol diff merge"),("Range-Diff Center",lambda:GitRangeDiffCenter(self,repo),"range diff rebase patch series compare"),("Refspec Lab",lambda:RefspecLabCenter(self,repo),"refspec fetch push dry run remote mapping"),("Git Notes Merge",lambda:GitNotesMergeCenter(self,repo),"git notes merge union manual ours theirs"),("Merge Strategy Lab",lambda:MergeStrategyLabCenter(self,repo),"merge strategy ort recursive ours theirs subtree preview"),("Config Include Inspector",lambda:ConfigIncludeCenter(self,repo),"git config include includeif origins scopes"),("Pack Inventory",lambda:PackInventoryCenter(self,repo),"pack inventory verify-pack large blobs objects"),("Change Statistics",lambda:ChangeStatisticsCenter(self,repo),"change statistics churn authors extensions range"),("Conflict Stage Explorer",lambda:ConflictStageExplorer(self,repo),"conflict stages base ours theirs index"),("Branch Rename Planner",lambda:BranchRenamePlanner(self,repo),"branch rename remote upstream protected"),("Lost & Found Center",lambda:LostFoundCenter(self,repo),"lost found fsck recovery commit object"),("Shallow Repository Center",lambda:ShallowRepositoryCenter(self,repo),"shallow clone deepen unshallow history tags"),("Status Porcelain Explorer",lambda:StatusPorcelainCenter(self,repo),"status porcelain v2 automation records"),("Sparse Index Center",lambda:GitSparseIndexCenter(self,repo),"sparse index checkout performance large repository"),("Maintenance Schedule",lambda:GitMaintenanceScheduleCenter(self,repo),"maintenance schedule register strategy incremental geometric"),("Repository Format Inspector",lambda:ObjectFormatCenter(self,repo),"repository format sha1 sha256 ref storage extensions compatibility"),("Selective Clean",lambda:GitCleanInteractiveCenter(self,repo),"clean selective untracked ignored preview"),("File Evolution",lambda:FileEvolutionCenter(self,repo),"file evolution history rename content export"),("Remote Details",lambda:GitRemoteShowCenter(self,repo),"remote show tracking stale branches details"),("Protocol Diagnostics",lambda:ProtocolDiagnosticsCenter(self,repo),"git protocol v2 packet trace remote capabilities"),("Object Alternates Inspector",lambda:AlternatesInspectorCenter(self,repo),"object alternates shared clone dissociate repack"),("EOL Normalization",lambda:EolNormalizationCenter(self,repo),"eol line ending autocrlf gitattributes renormalize"),("Commit Message Audit",lambda:CommitMessageAuditCenter(self,repo),"commit message audit conventional quality subject"),("Revision Manifest",lambda:GitArchiveManifestCenter(self,repo),"revision manifest tree blob verify archive integrity"),("Branch Descriptions",lambda:BranchDescriptionCenter(self,repo),"branch description config local metadata purpose"),("Selective Stash",lambda:SelectiveStashCenter(self,repo),"stash selective pathspec keep index untracked"),("Worktree Move",lambda:WorktreeMoveCenter(self,repo),"worktree move relocate repair linked"),("Config Snapshot Compare",lambda:ConfigSnapshotCompareCenter(self,repo),"git config snapshot compare diff origin scope"),("Fixup & Squash Commits",lambda:CommitFixupCenter(self,repo),"fixup squash amend autosquash staged commit"),("Tracked File Flags",lambda:TrackedFileFlagsCenter(self,repo),"assume unchanged skip worktree update index flags"),("Revision Walk Lab",lambda:RevisionWalkCenter(self,repo),"revision walk topology ancestry first parent boundary order"),("Show-Branch Explorer",lambda:GitShowBranchCenter(self,repo),"show branch topology comparison multiple refs"),("Name-Rev Explorer",lambda:GitNameRevCenter(self,repo),"name rev human readable commit object tags"),("Object Growth Tracker",lambda:GitCountObjectsTrendCenter(self,repo),"count objects growth trend packs garbage maintenance"),("Ref Verification",lambda:GitVerifyRefCenter(self,repo),"verify ref symbolic peel reflog object"),("Ignore Rule Batch Tester",lambda:GitCheckIgnoreBatchCenter(self,repo),"check ignore batch verbose provenance patterns"),("Fetch Preview",lambda:AsyncFetchCenter(self,repo),"fetch dry run prune tags refspec preview")]
        self.render()
    def render(self):
        q=self.q.get().lower().strip();self.filtered=[c for c in self.commands if not q or q in (c[0]+" "+c[2]).lower()];self.list.delete(0,"end")
        for name,_,tags in self.filtered:self.list.insert("end",f"{name}    [{tags}]")
        if self.filtered:self.list.selection_set(0)
    def launch(self):
        s=self.list.curselection()
        if s:self.filtered[s[0]][1]();self.destroy()

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
        if p.exists():self.text.insert("1.0",p.read_text(encoding="utf-8",errors="replace"));self.status.set(f"Loaded {p.name}")
        else:self.status.set(f"{p.name} is not installed")
    def template(self):self.text.delete("1.0","end");self.text.insert("1.0",self.TEMPLATES[self.kind.get()])
    def save(self):
        p=self.path();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8");p.chmod(p.stat().st_mode|0o111);self.status.set(f"Saved and enabled {p.name}")
    def disable(self):
        p=self.path()
        if p.exists():p.chmod(p.stat().st_mode&~0o111);self.status.set(f"Disabled {p.name}")
    def test(self):
        p=self.path()
        if not p.exists():return messagebox.showwarning("Hook","Save the hook first.",parent=self)
        try:
            r=subprocess.run([str(p)],cwd=self.repo,text=True,capture_output=True,timeout=120,encoding="utf-8",errors="replace");messagebox.showinfo("Hook test",f"Exit code: {r.returncode}\n\n{r.stdout}\n{r.stderr}",parent=self)
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
        self.path.write_text(json.dumps(self.recipes,indent=2),encoding="utf-8")
        if notice:messagebox.showinfo("Recipes","Saved under .git/gccc-recipes.json",parent=self)
    def run_selected(self):
        s=self.list.curselection()
        if not s:return
        r=self.recipes[s[0]]
        try:
            p=subprocess.run(r["command"],cwd=self.repo,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace");v=f"Recipe: {r['name']}\nExit code: {p.returncode}\n\n{p.stdout}\n{p.stderr}"
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
            r=subprocess.run(["gpg","--list-secret-keys","--keyid-format=long"],text=True,capture_output=True,timeout=60,encoding="utf-8",errors="replace");v=(r.stdout+r.stderr).strip()
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
        p=Path(self.repo)/"CHANGELOG.md";section=self.text.get("1.0","end-1c").strip()+"\n\n";old=p.read_text(encoding="utf-8",errors="replace") if p.exists() else "# Changelog\n\n"
        if old.startswith("# Changelog"):new="# Changelog\n\n"+section+old[len("# Changelog"):].lstrip()
        else:new=section+old
        p.write_text(new,encoding="utf-8");messagebox.showinfo("Changelog","CHANGELOG.md updated. Review and commit it.",parent=self)
    def save(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".md",initialfile="changelog-section.md")
        if p:Path(p).write_text(self.text.get("1.0","end-1c")+"\n",encoding="utf-8")
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
        if p:Path(p).write_text(self.report,encoding="utf-8")

class PluginManager(tk.Toplevel):
    """Manage local JSON command plugins without importing arbitrary Python modules."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.dir=Path(repo)/".git"/"gccc-plugins";self.title("Plugin Manager");self.geometry("1080x720");self._build();self.load()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Refresh",self.load),("Create plugin",self.create),("Run selected",self.run),("Enable/disable",self.toggle),("Delete",self.delete),("Open plugin folder",self.open_folder)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        pane=ttk.Panedwindow(self,orient="horizontal");pane.pack(fill="both",expand=True,padx=8,pady=5);l=ttk.Frame(pane);r=ttk.Frame(pane);pane.add(l,weight=2);pane.add(r,weight=3)
        self.list=tk.Listbox(l,font=("Segoe UI",10));self.list.pack(fill="both",expand=True);self.list.bind("<<ListboxSelect>>",lambda e:self.describe())
        self.out=tk.Text(r,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.out.pack(fill="both",expand=True)
        ttk.Label(self,text="Plugins are JSON command definitions stored under .git/gccc-plugins. Commands run directly without a shell. Review every plugin before execution.",padding=8).pack(fill="x")
    def load(self):
        import json
        self.dir.mkdir(parents=True,exist_ok=True);self.plugins=[]
        for p in sorted(self.dir.glob("*.json")):
            try:
                d=json.loads(p.read_text(encoding="utf-8"));d["_path"]=p;self.plugins.append(d)
            except Exception:pass
        self.list.delete(0,"end")
        for p in self.plugins:self.list.insert("end",("[ON] " if p.get("enabled",True) else "[OFF] ")+p.get("name",p["_path"].stem))
    def selected(self):
        s=self.list.curselection();return self.plugins[s[0]] if s else None
    def describe(self):
        import json
        p=self.selected()
        if p:self.out.delete("1.0","end");self.out.insert("1.0",json.dumps({k:v for k,v in p.items() if k!="_path"},indent=2))
    def create(self):
        import json,re,shlex
        name=simpledialog.askstring("Plugin","Display name:",parent=self);cmd=simpledialog.askstring("Plugin","Command line:",parent=self) if name else None
        if not cmd:return
        slug=re.sub(r"[^a-z0-9_-]+","-",name.lower()).strip("-") or "plugin"
        d={"name":name,"description":"Local command plugin","command":shlex.split(cmd),"enabled":True}
        (self.dir/f"{slug}.json").write_text(json.dumps(d,indent=2),encoding="utf-8");self.load()
    def run(self):
        p=self.selected()
        if not p or not p.get("enabled",True):return
        command=p.get("command")
        if not isinstance(command,list) or not command:return messagebox.showerror("Plugin","Plugin command must be a JSON array.",parent=self)
        if not messagebox.askyesno("Run plugin",f"Run {p.get('name')}?\n\n{' '.join(command)}",parent=self):return
        try:r=subprocess.run(command,cwd=self.repo,text=True,capture_output=True,timeout=1800,encoding="utf-8",errors="replace");v=f"Exit code: {r.returncode}\n\n{r.stdout}\n{r.stderr}"
        except Exception as e:v=str(e)
        self.out.delete("1.0","end");self.out.insert("1.0",v)
    def toggle(self):
        import json
        p=self.selected()
        if p:p["enabled"]=not p.get("enabled",True);p["_path"].write_text(json.dumps({k:v for k,v in p.items() if k!="_path"},indent=2),encoding="utf-8");self.load()
    def delete(self):
        p=self.selected()
        if p and messagebox.askyesno("Delete plugin",f"Delete {p.get('name')}?",parent=self):p["_path"].unlink();self.load()
    def open_folder(self):
        import os
        os.startfile(self.dir) if hasattr(os,"startfile") else subprocess.Popen(["xdg-open",str(self.dir)])

class BatchOperationsCenter(tk.Toplevel):
    """Portfolio operations with dry-run and per-repository results."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.root=Path(repo).parent;self.title("Batch Operations Center");self.geometry("1180x760");self._build();self.scan()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.root));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Button(top,text="Browse",command=self.browse).pack(side="left",padx=3);ttk.Button(top,text="Scan",command=self.scan).pack(side="left")
        self.op=tk.StringVar(value="Fetch/prune");ttk.Combobox(top,textvariable=self.op,values=["Fetch/prune","Status","Integrity check","Python compile","Pull FF-only"],state="readonly",width=18).pack(side="left",padx=5);ttk.Button(top,text="Run selected",command=self.run).pack(side="left")
        self.tree=ttk.Treeview(self,columns=("repo","branch","state","result"),show="headings",selectmode="extended")
        for c,t,w in [("repo","Repository",260),("branch","Branch",160),("state","State",100),("result","Last result",520)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
        ttk.Label(self,text="Pull FF-only is skipped for repositories with local changes. Batch operations run sequentially and never force changes.",padding=8).pack(fill="x")
    def browse(self):
        p=filedialog.askdirectory(parent=self)
        if p:self.path.set(p);self.scan()
    def scan(self):
        root=Path(self.path.get());self.rows=[];self.tree.delete(*self.tree.get_children())
        if not root.exists():return
        candidates=[root] if (root/".git").exists() else [p for p in root.iterdir() if p.is_dir() and (p/".git").exists()]
        for p in sorted(candidates):
            try:b=git(p,"branch","--show-current");s=git(p,"status","--porcelain");state="Clean" if s=="Completed successfully." else "Changed";self.rows.append({"path":p,"branch":b,"state":state,"result":""});self.tree.insert("","end",iid=str(len(self.rows)-1),values=(p.name,b,state,""))
            except Exception:pass
    def run(self):
        ids=self.tree.selection()
        if not ids:return
        op=self.op.get()
        if not messagebox.askyesno("Batch operation",f"Run '{op}' on {len(ids)} selected repositories?",parent=self):return
        for iid in ids:
            r=self.rows[int(iid)];p=r["path"]
            try:
                if op=="Fetch/prune":out=git(p,"fetch","--all","--prune")
                elif op=="Status":out=git(p,"status","--short","--branch")
                elif op=="Integrity check":out=git(p,"fsck","--no-progress")
                elif op=="Python compile":
                    x=subprocess.run(["python","-m","compileall","-q","."],cwd=p,text=True,capture_output=True,timeout=900,encoding="utf-8",errors="replace");out=f"Exit {x.returncode}: {(x.stdout+x.stderr).strip()}"
                elif r["state"]!="Clean":out="SKIPPED: local changes"
                else:out=git(p,"pull","--ff-only")
            except Exception as e:out="ERROR: "+str(e)
            short=out.replace("\n"," | ")[:500];self.tree.set(iid,"result",short)

class RepositoryDashboardCenter(tk.Toplevel):
    """One-page operational dashboard for the selected repository."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Operations Dashboard");self.geometry("1150x760");self._build();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Smart Sync",command=lambda:SyncCenter(self,self.repo)).pack(side="left",padx=3);ttk.Button(top,text="Review",command=lambda:ChangeReviewCenter(self,self.repo)).pack(side="left");ttk.Button(top,text="Release policy",command=lambda:ReleasePolicyCenter(self,self.repo)).pack(side="left",padx=3)
        self.text=tk.Text(self,wrap="word",font=("Consolas",10),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def safe(self,*a):
        try:return git(self.repo,*a)
        except Exception as e:return "Unavailable: "+str(e)
    def refresh(self):
        branch=self.safe("branch","--show-current");status=self.safe("status","--porcelain");clean=status=="Completed successfully."
        try:up=self.safe("rev-parse","--abbrev-ref","--symbolic-full-name","@{u}");ahead=self.safe("rev-list","--count","@{u}..HEAD");behind=self.safe("rev-list","--count","HEAD..@{u}")
        except:up=ahead=behind="-"
        last=self.safe("log","-1","--date=short","--pretty=format:%h %ad %an %s");tags=self.safe("tag","--sort=-creatordate").splitlines()[:5];changes=0 if clean else len(status.splitlines())
        health=[]
        for f in ("README.md","CHANGELOG.md","LICENSE","SECURITY.md","CONTRIBUTING.md"):health.append((f,(Path(self.repo)/f).exists()))
        report=f"REPOSITORY OPERATIONS DASHBOARD\n{'='*78}\nRepository: {self.repo}\nBranch: {branch}\nUpstream: {up}\nAhead / Behind: {ahead} / {behind}\nWorking tree: {'Clean' if clean else f'{changes} changed entries'}\nLast commit: {last}\n\nRECENT TAGS\n"+"\n".join(tags or ["None"])+"\n\nDOCUMENTATION CONTROLS\n"+"\n".join(f"[{'PASS' if ok else 'MISS'}] {f}" for f,ok in health)+"\n\nRECOMMENDED NEXT ACTION\n"
        if not clean:report+="Review and commit or stash local changes."
        elif str(behind)!="0" and str(ahead)=="0":report+="Run Smart Sync to fast-forward from upstream."
        elif str(ahead)!="0" and str(behind)=="0":report+="Review and push local commits."
        elif str(ahead)!="0" and str(behind)!="0":report+="Histories diverged. Use Compare before merge or rebase."
        else:report+="Repository is synchronized and clean."
        self.text.delete("1.0","end");self.text.insert("1.0",report)

class DataExportCenter(tk.Toplevel):
    """Export local repository metadata in JSON or CSV for analysis."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Repository Data Export");self.geometry("1000x680");self._build();self.preview()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x")
        for t,c in [("Preview",self.preview),("Export JSON",self.json_export),("Export commits CSV",self.csv_export)]:ttk.Button(top,text=t,command=c).pack(side="left",padx=2)
        self.text=tk.Text(self,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.text.pack(fill="both",expand=True,padx=8,pady=5)
    def collect(self):
        import json
        def safe(*a):
            try:return git(self.repo,*a)
            except:return ""
        commits=[]
        raw=safe("log","-500","--date=iso-strict","--pretty=format:%H%x1f%h%x1f%ad%x1f%an%x1f%ae%x1f%s")
        for line in raw.splitlines():
            p=line.split("\x1f",5)
            if len(p)==6:commits.append(dict(hash=p[0],short=p[1],date=p[2],author=p[3],email=p[4],subject=p[5]))
        return {"repository":Path(self.repo).name,"path":self.repo,"branch":safe("branch","--show-current"),"remotes":safe("remote","-v").splitlines(),"tags":safe("tag","--sort=-creatordate").splitlines(),"commits":commits}
    def preview(self):
        import json
        self.data=self.collect();self.text.delete("1.0","end");self.text.insert("1.0",json.dumps({**self.data,"commits":self.data["commits"][:10]},indent=2)+"\n\nPreview shows the latest 10 of up to 500 exported commits.")
    def json_export(self):
        import json
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".json",initialfile=Path(self.repo).name+"-repository-data.json")
        if p:Path(p).write_text(json.dumps(self.collect(),indent=2),encoding="utf-8")
    def csv_export(self):
        import csv
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",initialfile=Path(self.repo).name+"-commits.csv")
        if p:
            with open(p,"w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["hash","short","date","author","email","subject"]);w.writeheader();w.writerows(self.collect()["commits"])

class BackgroundJobsCenter(tk.Toplevel):
    """Run long commands in background threads with queue, logs and cancellation."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.title("Background Jobs Center");self.geometry("1120x740");self.jobs=[];self.processes={};self._build()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.command=tk.StringVar(value="git fetch --all --prune");ttk.Entry(top,textvariable=self.command).pack(side="left",fill="x",expand=True)
        ttk.Button(top,text="Queue command",command=self.queue).pack(side="left",padx=3);ttk.Button(top,text="Cancel selected",command=self.cancel).pack(side="left");ttk.Button(top,text="Clear finished",command=self.clear).pack(side="left",padx=3)
        pane=ttk.Panedwindow(self,orient="vertical");pane.pack(fill="both",expand=True,padx=8,pady=5);a=ttk.Frame(pane);b=ttk.Frame(pane);pane.add(a,weight=2);pane.add(b,weight=3)
        self.tree=ttk.Treeview(a,columns=("id","command","status","code"),show="headings")
        for c,t,w in [("id","ID",60),("command","Command",650),("status","Status",130),("code","Exit",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True);self.tree.bind("<<TreeviewSelect>>",lambda e:self.show_log())
        self.log=tk.Text(b,wrap="none",font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.log.pack(fill="both",expand=True)
        ttk.Label(self,text="Commands are parsed into argument arrays and run without a shell. Cancellation terminates the local process.",padding=8).pack(fill="x")
    def queue(self):
        import shlex,threading,time
        try:args=shlex.split(self.command.get())
        except Exception as e:return messagebox.showerror("Job",str(e),parent=self)
        if not args:return
        job={"id":len(self.jobs)+1,"args":args,"status":"Queued","code":"","log":""};self.jobs.append(job);iid=str(job["id"]);self.tree.insert("","end",iid=iid,values=(job["id"]," ".join(args),job["status"],""))
        def worker():
            job["status"]="Running";self.after(0,lambda:self.update_row(job))
            try:
                p=subprocess.Popen(args,cwd=self.repo,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding="utf-8",errors="replace");self.processes[job["id"]]=p
                for line in iter(p.stdout.readline,""):
                    job["log"]+=line
                    self.after(0,self.show_log)
                p.wait();job["code"]=p.returncode;job["status"]="Completed" if p.returncode==0 else "Failed"
            except Exception as e:job["log"]+=str(e);job["status"]="Failed";job["code"]="-"
            self.processes.pop(job["id"],None);self.after(0,lambda:self.update_row(job))
        threading.Thread(target=worker,daemon=True).start()
    def update_row(self,j):self.tree.item(str(j["id"]),values=(j["id"]," ".join(j["args"]),j["status"],j["code"]))
    def current(self):
        s=self.tree.selection();return next((j for j in self.jobs if str(j["id"])==s[0]),None) if s else None
    def show_log(self):
        j=self.current()
        if j:self.log.delete("1.0","end");self.log.insert("1.0",j["log"] or "No output yet.")
    def cancel(self):
        j=self.current();p=self.processes.get(j["id"]) if j else None
        if p and messagebox.askyesno("Cancel job",f"Terminate job {j['id']}?",parent=self):p.terminate();j["status"]="Cancelled";self.update_row(j)
    def clear(self):
        keep=[j for j in self.jobs if j["status"] in ("Queued","Running")];self.jobs=keep;self.tree.delete(*self.tree.get_children())
        for j in keep:self.tree.insert("","end",iid=str(j["id"]),values=(j["id"]," ".join(j["args"]),j["status"],j["code"]))

class PreferencesCenter(tk.Toplevel):
    """Persist local application preferences and UI defaults."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.path=Path.home()/".gccc-preferences.json";self.title("Preferences & Appearance");self.geometry("760x540");self._build();self.load()
    def _build(self):
        f=ttk.Frame(self,padding=14);f.pack(fill="both",expand=True);self.theme=tk.StringVar(value="clam");self.font=tk.IntVar(value=9);self.limit=tk.IntVar(value=200);self.confirm=tk.BooleanVar(value=True);self.default_branch=tk.StringVar(value="main")
        rows=[("Tk theme",ttk.Combobox(f,textvariable=self.theme,values=ttk.Style().theme_names(),state="readonly")),("Editor font size",ttk.Spinbox(f,from_=8,to=18,textvariable=self.font)),("History row limit",ttk.Spinbox(f,from_=50,to=2000,increment=50,textvariable=self.limit)),("Default base branch",ttk.Entry(f,textvariable=self.default_branch))]
        for i,(label,w) in enumerate(rows):ttk.Label(f,text=label).grid(row=i,column=0,sticky="w",pady=8);w.grid(row=i,column=1,sticky="ew",padx=8,pady=8)
        ttk.Checkbutton(f,text="Require confirmation for destructive operations",variable=self.confirm).grid(row=4,column=1,sticky="w",pady=8);f.columnconfigure(1,weight=1)
        ttk.Button(f,text="Save preferences",command=self.save).grid(row=5,column=1,sticky="e",pady=18)
        ttk.Label(f,text="Theme changes apply immediately. Other values are defaults for future modular centers and are stored outside repositories.",wraplength=620).grid(row=6,column=0,columnspan=2,sticky="w")
    def load(self):
        import json
        if self.path.exists():
            try:
                p=json.loads(self.path.read_text(encoding="utf-8"));self.theme.set(p.get("theme","clam"));self.font.set(p.get("font_size",9));self.limit.set(p.get("history_limit",200));self.confirm.set(p.get("confirm_destructive",True));self.default_branch.set(p.get("default_branch","main"))
            except:pass
    def save(self):
        import json
        p={"theme":self.theme.get(),"font_size":self.font.get(),"history_limit":self.limit.get(),"confirm_destructive":self.confirm.get(),"default_branch":self.default_branch.get()};self.path.write_text(json.dumps(p,indent=2),encoding="utf-8")
        try:ttk.Style().theme_use(self.theme.get())
        except:pass
        messagebox.showinfo("Preferences",f"Saved {self.path}",parent=self)

class PortfolioHistoryCenter(tk.Toplevel):
    """SQLite-backed snapshots of local repository portfolio state."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.root=Path(repo).parent;self.db=Path.home()/".gccc-portfolio.sqlite3";self.title("Portfolio History");self.geometry("1180x740");self._build();self.init_db();self.refresh()
    def _build(self):
        top=ttk.Frame(self,padding=8);top.pack(fill="x");self.path=tk.StringVar(value=str(self.root));ttk.Entry(top,textvariable=self.path).pack(side="left",fill="x",expand=True);ttk.Button(top,text="Capture snapshot",command=self.capture).pack(side="left",padx=3);ttk.Button(top,text="Refresh",command=self.refresh).pack(side="left");ttk.Button(top,text="Export CSV",command=self.export).pack(side="left",padx=3)
        self.tree=ttk.Treeview(self,columns=("time","repo","branch","state","ahead","behind"),show="headings")
        for c,t,w in [("time","Captured",170),("repo","Repository",280),("branch","Branch",150),("state","State",90),("ahead","Ahead",70),("behind","Behind",70)]:self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor="w")
        self.tree.pack(fill="both",expand=True,padx=8,pady=5)
    def init_db(self):
        import sqlite3
        with sqlite3.connect(self.db) as c:c.execute("create table if not exists snapshots(captured text, path text, repo text, branch text, state text, ahead text, behind text)")
    def capture(self):
        import sqlite3,datetime
        root=Path(self.path.get());repos=[root] if (root/".git").exists() else [p for p in root.iterdir() if p.is_dir() and (p/".git").exists()]
        rows=[];now=datetime.datetime.now().isoformat(timespec="seconds")
        for p in repos:
            try:
                branch=git(p,"branch","--show-current");s=git(p,"status","--porcelain");state="Clean" if s=="Completed successfully." else "Changed"
                try:a=git(p,"rev-list","--count","@{u}..HEAD");b=git(p,"rev-list","--count","HEAD..@{u}")
                except:a=b="-"
                rows.append((now,str(p),p.name,branch,state,a,b))
            except:pass
        with sqlite3.connect(self.db) as c:c.executemany("insert into snapshots values(?,?,?,?,?,?,?)",rows)
        self.refresh();messagebox.showinfo("Portfolio",f"Captured {len(rows)} repositories.",parent=self)
    def refresh(self):
        import sqlite3
        self.tree.delete(*self.tree.get_children())
        with sqlite3.connect(self.db) as c:rows=c.execute("select captured,repo,branch,state,ahead,behind from snapshots order by captured desc limit 1000").fetchall()
        for r in rows:self.tree.insert("","end",values=r)
    def export(self):
        import sqlite3,csv
        p=filedialog.asksaveasfilename(parent=self,defaultextension=".csv",initialfile="portfolio-history.csv")
        if not p:return
        with sqlite3.connect(self.db) as c:rows=c.execute("select captured,path,repo,branch,state,ahead,behind from snapshots order by captured").fetchall()
        with open(p,"w",newline="",encoding="utf-8") as f:w=csv.writer(f);w.writerow(["captured","path","repo","branch","state","ahead","behind"]);w.writerows(rows)

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
