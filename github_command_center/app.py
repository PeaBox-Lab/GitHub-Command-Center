
import os
import threading
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
import webbrowser

from .config import load_config, save_config
from .github_api import GitHubClient
from .git_ops import clone_repo, git_available, pull_repo, status_repo
from .local_git_gui import LocalGitWindow

BG = "#f5f7fb"
NAV = "#0d1526"
PURPLE = "#4f46e5"
TEXT = "#172033"
MUTED = "#64748b"


class GitHubCommandCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GitHub Command Center 3.2")
        self.geometry("1400x860")
        self.minsize(1120, 720)
        self.configure(bg=BG)
        self.config_data = load_config()
        self.client = None
        self.user = {}
        self.repos = []
        self.filtered = []
        self.events = []
        self.rate = {}
        self.current_view = "Dashboard"
        self.status_var = tk.StringVar(value="Not connected")
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="Recently updated")
        self._style()
        self._shell()
        self.show_connect()

    def _style(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10), padding=8)
        style.map("Treeview", background=[("selected", "#e0e7ff")], foreground=[("selected", TEXT)])
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Accent.TButton", background=PURPLE, foreground="white")
        style.map("Accent.TButton", background=[("active", "#4338ca")])

    def _shell(self):
        self.nav = tk.Frame(self, bg=NAV, width=220)
        self.nav.pack(side="left", fill="y")
        self.nav.pack_propagate(False)
        tk.Label(self.nav, text="◉  GitHub Command", bg=NAV, fg="white", font=("Segoe UI Semibold", 15)).pack(anchor="w", padx=18, pady=(24, 4))
        tk.Label(self.nav, text="Python desktop console", bg=NAV, fg="#7c8aa5", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 24))
        self.nav_buttons = {}
        for name in ["Dashboard", "Repositories", "Local Git", "Activity", "Insights", "Settings"]:
            b = tk.Button(self.nav, text=name, command=lambda n=name: self.switch(n), anchor="w", relief="flat", bd=0,
                          bg=NAV, fg="#cbd5e1", activebackground="#1e293b", activeforeground="white",
                          font=("Segoe UI", 10), padx=18, pady=12, cursor="hand2")
            b.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = b
        tk.Label(self.nav, textvariable=self.status_var, bg="#111c31", fg="#a5b4fc", wraplength=180,
                 font=("Segoe UI", 9), padx=10, pady=12).pack(side="bottom", fill="x", padx=12, pady=14)

        self.right = tk.Frame(self, bg=BG)
        self.right.pack(side="left", fill="both", expand=True)
        self.header = tk.Frame(self.right, bg="white", height=76, highlightthickness=1, highlightbackground="#e2e8f0")
        self.header.pack(fill="x"); self.header.pack_propagate(False)
        self.title_label = tk.Label(self.header, text="Dashboard", bg="white", fg=TEXT, font=("Segoe UI Semibold", 18))
        self.title_label.pack(side="left", padx=28)
        ttk.Button(self.header, text="Refresh", command=self.refresh).pack(side="right", padx=(8, 24), pady=18)
        ttk.Button(self.header, text="New repository", style="Accent.TButton", command=self.new_repository).pack(side="right", pady=18)
        self.content = tk.Frame(self.right, bg=BG)
        self.content.pack(fill="both", expand=True, padx=24, pady=20)

    def clear(self):
        for w in self.content.winfo_children(): w.destroy()

    def card(self, parent, title=None):
        frame = tk.Frame(parent, bg="white", highlightthickness=1, highlightbackground="#e2e8f0")
        if title: tk.Label(frame, text=title, bg="white", fg=TEXT, font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=16, pady=(14, 8))
        return frame

    def run_async(self, job, done=None):
        self.status_var.set("Working...")
        def work():
            try:
                value = job()
                self.after(0, lambda: self._finish(value, done))
            except Exception as exc:
                self.after(0, lambda: self._fail(exc))
        threading.Thread(target=work, daemon=True).start()

    def _finish(self, value, done):
        self.status_var.set(f"Connected: {self.user.get('login', '')}" if self.client else "Not connected")
        if done: done(value)

    def _fail(self, exc):
        self.status_var.set("Operation failed")
        messagebox.showerror("GitHub Command Center", str(exc))

    def show_connect(self):
        self.clear(); self.title_label.config(text="Connect to GitHub")
        box = self.card(self.content, "Connect your GitHub account")
        box.place(relx=.5, rely=.42, anchor="center", width=590, height=360)
        tk.Label(box, text="Use a fine-grained personal access token. The token is kept in memory only and is not written to disk.",
                 bg="white", fg=MUTED, wraplength=520, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(10, 16))
        tk.Label(box, text="Personal access token", bg="white", fg=TEXT, font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=24)
        token = ttk.Entry(box, show="•", font=("Segoe UI", 11))
        token.pack(fill="x", padx=24, pady=(7, 12), ipady=6); token.focus_set()
        remember = tk.BooleanVar(value=False)
        tk.Checkbutton(box, text="Remember token using optional system keyring", variable=remember, bg="white", fg=TEXT,
                       activebackground="white").pack(anchor="w", padx=21)
        def connect():
            value = token.get().strip()
            if not value: return messagebox.showwarning("Token required", "Enter a GitHub token.")
            self.client = GitHubClient(value)
            def loaded(data):
                if remember.get():
                    try:
                        import keyring
                        keyring.set_password("GitHubCommandCenter", "token", value)
                    except Exception as exc:
                        messagebox.showwarning("Keyring", f"Connected, but the token could not be saved: {exc}")
                self.user, self.repos, self.events, self.rate = data
                self.status_var.set(f"Connected: {self.user.get('login')}")
                self.switch("Dashboard")
            self.run_async(lambda: self._load_all(), loaded)
        ttk.Button(box, text="Connect account", style="Accent.TButton", command=connect).pack(anchor="w", padx=24, pady=18)
        tk.Label(box, text="Tip: grant repository Metadata read access. Add Issues read/write and Administration write only for those actions.",
                 bg="#fff7ed", fg="#9a3412", wraplength=520, justify="left", padx=12, pady=10).pack(fill="x", padx=24)
        self.after(100, self._try_keyring)

    def _try_keyring(self):
        if self.client: return
        try:
            import keyring
            token = keyring.get_password("GitHubCommandCenter", "token")
            if token:
                self.client = GitHubClient(token)
                self.run_async(self._load_all, self._loaded_from_keyring)
        except Exception:
            pass

    def _loaded_from_keyring(self, data):
        self.user, self.repos, self.events, self.rate = data
        self.switch("Dashboard")

    def _load_all(self):
        user = self.client.get_user()
        repos = self.client.get_repositories()
        events = self.client.get_events(user["login"])
        rate = self.client.get_rate_limit()
        return user, repos, events, rate

    def refresh(self):
        if not self.client: return self.show_connect()
        self.run_async(self._load_all, self._on_refresh)

    def _on_refresh(self, data):
        self.user, self.repos, self.events, self.rate = data
        self.switch(self.current_view)

    def switch(self, name):
        if not self.client and name != "Settings": return self.show_connect()
        self.current_view = name; self.title_label.config(text=name)
        for n,b in self.nav_buttons.items(): b.config(bg=PURPLE if n == name else NAV, fg="white" if n == name else "#cbd5e1")
        self.view_local_git() if name == "Local Git" else getattr(self, f"view_{name.lower()}")()

    def view_dashboard(self):
        self.clear()
        welcome = tk.Frame(self.content, bg="#312e81", height=122); welcome.pack(fill="x"); welcome.pack_propagate(False)
        tk.Label(welcome, text=f"Welcome, {self.user.get('name') or self.user.get('login')}", bg="#312e81", fg="white", font=("Segoe UI Semibold", 22)).pack(anchor="w", padx=24, pady=(22, 4))
        tk.Label(welcome, text="Your repositories, activity and maintenance signals in one workspace.", bg="#312e81", fg="#c7d2fe", font=("Segoe UI", 10)).pack(anchor="w", padx=24)
        stats = [("Repositories", len(self.repos)), ("Stars", sum(r.get("stargazers_count",0) for r in self.repos)), ("Forks", sum(r.get("forks_count",0) for r in self.repos)), ("Open issues", sum(r.get("open_issues_count",0) for r in self.repos))]
        row=tk.Frame(self.content,bg=BG); row.pack(fill="x", pady=16)
        for label,value in stats:
            c=self.card(row); c.pack(side="left",fill="both",expand=True,padx=5)
            tk.Label(c,text=label,bg="white",fg=MUTED,font=("Segoe UI",9)).pack(anchor="w",padx=14,pady=(13,2))
            tk.Label(c,text=str(value),bg="white",fg=TEXT,font=("Segoe UI Semibold",22)).pack(anchor="w",padx=14,pady=(0,12))
        recent=self.card(self.content,"Recently updated repositories"); recent.pack(fill="both",expand=True)
        self.repo_tree(recent, self.repos[:12])

    def repo_tree(self, parent, repos):
        cols=("name","visibility","language","stars","issues","updated")
        tree=ttk.Treeview(parent,columns=cols,show="headings")
        labels={"name":"Repository","visibility":"Visibility","language":"Language","stars":"Stars","issues":"Issues","updated":"Updated"}
        for c in cols: tree.heading(c,text=labels[c]); tree.column(c,width=130 if c!="name" else 260,anchor="w")
        for r in repos:
            tree.insert("", "end", iid=str(r["id"]), values=(r["full_name"],r.get("visibility","private" if r.get("private") else "public"),r.get("language") or "–",r.get("stargazers_count",0),r.get("open_issues_count",0),self.age(r.get("updated_at"))))
        tree.pack(fill="both",expand=True,padx=14,pady=(4,14))
        tree.bind("<Double-1>",lambda e:self.open_selected(tree))
        return tree

    def view_repositories(self):
        self.clear()
        tools=tk.Frame(self.content,bg=BG); tools.pack(fill="x",pady=(0,10))
        entry=ttk.Entry(tools,textvariable=self.search_var); entry.pack(side="left",fill="x",expand=True,ipady=5)
        entry.bind("<KeyRelease>",lambda e:self._filter_repos())
        ttk.Combobox(tools,textvariable=self.sort_var,values=["Recently updated","Name","Most stars"],state="readonly",width=18).pack(side="left",padx=8)
        self.sort_var.trace_add("write",lambda *_:self._filter_repos())
        ttk.Button(tools,text="Create issue",command=self.new_issue).pack(side="left",padx=4)
        ttk.Button(tools,text="Clone",command=self.clone_selected).pack(side="left",padx=4)
        ttk.Button(tools,text="Open on GitHub",command=lambda:self.open_selected(self.repo_table)).pack(side="left",padx=4)
        box=self.card(self.content); box.pack(fill="both",expand=True)
        self.repo_table=self.repo_tree(box,self.repos); self._filter_repos()

    def _filter_repos(self):
        if not hasattr(self,"repo_table"): return
        q=self.search_var.get().lower()
        data=[r for r in self.repos if q in (r.get("full_name","")+" "+(r.get("description") or "")+" "+(r.get("language") or "")).lower()]
        if self.sort_var.get()=="Name": data.sort(key=lambda r:r["name"].lower())
        elif self.sort_var.get()=="Most stars": data.sort(key=lambda r:r.get("stargazers_count",0),reverse=True)
        else: data.sort(key=lambda r:r.get("updated_at", ""),reverse=True)
        self.repo_table.delete(*self.repo_table.get_children())
        for r in data:
            self.repo_table.insert("","end",iid=str(r["id"]),values=(r["full_name"],r.get("visibility","public"),r.get("language") or "–",r.get("stargazers_count",0),r.get("open_issues_count",0),self.age(r.get("updated_at"))))

    def selected_repo(self):
        if not hasattr(self,"repo_table") or not self.repo_table.selection():
            messagebox.showinfo("Select repository", "Select a repository first."); return None
        rid=int(self.repo_table.selection()[0]); return next((r for r in self.repos if r["id"]==rid),None)

    def open_selected(self, tree):
        if not tree.selection(): return
        rid=int(tree.selection()[0]); repo=next((r for r in self.repos if r["id"]==rid),None)
        if repo: webbrowser.open(repo["html_url"])

    def view_local_git(self):
        LocalGitWindow(self, self.config_data.get("last_repo", ""))

    def view_activity(self):
        self.clear(); box=self.card(self.content,"Recent public activity"); box.pack(fill="both",expand=True)
        tree=ttk.Treeview(box,columns=("type","repo","date"),show="headings")
        for c,t,w in [("type","Activity",180),("repo","Repository",420),("date","Date",180)]: tree.heading(c,text=t);tree.column(c,width=w,anchor="w")
        for e in self.events: tree.insert("","end",values=(e.get("type","").replace("Event",""),e.get("repo",{}).get("name",""),self.age(e.get("created_at"))))
        tree.pack(fill="both",expand=True,padx=14,pady=(4,14))

    def view_insights(self):
        self.clear()
        stale=[r for r in self.repos if self.days(r.get("updated_at"))>90]
        missing=[r for r in self.repos if not r.get("description")]
        langs={}
        for r in self.repos:
            if r.get("language"): langs[r["language"]]=langs.get(r["language"],0)+1
        for title,text in [("Stale repositories",f"{len(stale)} repositories have not been updated for more than 90 days."),("Missing descriptions",f"{len(missing)} repositories do not have a description."),("Language portfolio",", ".join(f"{k}: {v}" for k,v in sorted(langs.items(),key=lambda x:-x[1])) or "No language data"),("API allowance",f"{self.rate.get('remaining','–')} of {self.rate.get('limit','–')} requests remaining.")]:
            c=self.card(self.content,title); c.pack(fill="x",pady=6)
            tk.Label(c,text=text,bg="white",fg=MUTED,wraplength=850,justify="left",font=("Segoe UI",10)).pack(anchor="w",padx=16,pady=(0,16))

    def view_settings(self):
        self.clear(); box=self.card(self.content,"Application settings"); box.pack(fill="x")
        tk.Label(box,text="Local workspace",bg="white",fg=TEXT,font=("Segoe UI Semibold",10)).pack(anchor="w",padx=16,pady=(8,4))
        row=tk.Frame(box,bg="white"); row.pack(fill="x",padx=16,pady=(0,12))
        workspace=tk.StringVar(value=self.config_data.get("workspace",str(Path.home()/"GitHub")))
        ttk.Entry(row,textvariable=workspace).pack(side="left",fill="x",expand=True,ipady=5)
        ttk.Button(row,text="Browse",command=lambda:workspace.set(filedialog.askdirectory() or workspace.get())).pack(side="left",padx=6)
        def save(): self.config_data["workspace"]=workspace.get();save_config(self.config_data);messagebox.showinfo("Saved","Settings saved.")
        ttk.Button(box,text="Save settings",style="Accent.TButton",command=save).pack(anchor="w",padx=16,pady=(0,12))
        ttk.Button(box,text="Disconnect and forget token",command=self.disconnect).pack(anchor="w",padx=16,pady=(0,16))
        tk.Label(box,text=f"Git command available: {'Yes' if git_available() else 'No'}",bg="white",fg=MUTED).pack(anchor="w",padx=16,pady=(0,16))

    def new_repository(self):
        if not self.client: return self.show_connect()
        name=simpledialog.askstring("New repository","Repository name:",parent=self)
        if not name:return
        desc=simpledialog.askstring("New repository","Description (optional):",parent=self) or ""
        private=messagebox.askyesno("Visibility","Create as a private repository?")
        self.run_async(lambda:self.client.create_repository(name,desc,private,True),lambda r:(self.repos.insert(0,r),self.switch("Repositories"),messagebox.showinfo("Created",f"Created {r['full_name']}")))

    def new_issue(self):
        repo=self.selected_repo()
        if not repo:return
        title=simpledialog.askstring("New issue",f"Issue title for {repo['name']}:",parent=self)
        if not title:return
        body=simpledialog.askstring("New issue","Description:",parent=self) or ""
        self.run_async(lambda:self.client.create_issue(repo["full_name"],title,body),lambda i:messagebox.showinfo("Created",f"Issue #{i['number']} created."))

    def clone_selected(self):
        repo=self.selected_repo()
        if not repo:return
        workspace=self.config_data.get("workspace",str(Path.home()/"GitHub"))
        self.run_async(lambda:clone_repo(repo["clone_url"],workspace),lambda out:messagebox.showinfo("Clone",out))

    def disconnect(self):
        try:
            import keyring
            keyring.delete_password("GitHubCommandCenter","token")
        except Exception: pass
        self.client=None;self.user={};self.repos=[];self.events=[];self.rate={};self.status_var.set("Not connected");self.show_connect()

    @staticmethod
    def days(value):
        if not value:return 0
        dt=datetime.fromisoformat(value.replace("Z","+00:00"));return max(0,(datetime.now(timezone.utc)-dt).days)
    @classmethod
    def age(cls,value):
        d=cls.days(value)
        return "today" if d==0 else f"{d} day{'s' if d!=1 else ''} ago"


def main():
    GitHubCommandCenter().mainloop()
