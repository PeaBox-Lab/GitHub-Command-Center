from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import GitService

class HomeDashboard(tk.Toplevel):
    def __init__(self,parent,repo,open_tool=None):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.open_tool=open_tool;self.title('Home');self.geometry('1040x700');self._build();self.refresh()
    def _build(self):
        root=ttk.Frame(self,padding=16);root.pack(fill='both',expand=True)
        ttk.Label(root,text='Repository Home',font=('Segoe UI Semibold',18)).pack(anchor='w')
        self.summary=tk.StringVar();ttk.Label(root,textvariable=self.summary,font=('Segoe UI',10)).pack(anchor='w',pady=(4,14))
        actions=ttk.Frame(root);actions.pack(fill='x')
        for label,target in [('Review changes','Changes Center V2'),('Browse history','History Center V2'),('Pull / Push','Push & Pull Center'),('Run preflight','Review Center V2'),('GitHub','GitHub Network Center'),('Release','Release Publish Center V2')]:
            ttk.Button(actions,text=label,command=lambda t=target:self.launch(t)).pack(side='left',padx=3,pady=3)
        ttk.Separator(root).pack(fill='x',pady=14)
        self.alerts=tk.Text(root,height=8,wrap='word',font=('Segoe UI',10),bg='#f8fafc',fg='#111827');self.alerts.pack(fill='x')
        ttk.Label(root,text='Recent commits',font=('Segoe UI Semibold',11)).pack(anchor='w',pady=(14,4))
        self.recent=tk.Text(root,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.recent.pack(fill='both',expand=True)
        ttk.Button(root,text='Refresh',command=self.refresh).pack(anchor='e',pady=8)
    def launch(self,target):
        if self.open_tool:self.open_tool(target)
    def refresh(self):
        s=self.git.repository_state();self.summary.set(f'{self.repo}  |  Branch: {s.branch or "detached"}  |  Upstream: {s.upstream or "none"}  |  Ahead: {s.ahead if s.ahead is not None else "-"}  |  Behind: {s.behind if s.behind is not None else "-"}')
        warnings=[]
        if s.detached:warnings.append('Detached HEAD: recover or create a branch before publishing.')
        if not s.clean:warnings.append(f'{len(s.changed_paths)} changed path(s) need review.')
        if s.behind and s.behind>0:warnings.append(f'Current branch is {s.behind} commit(s) behind its upstream.')
        if not warnings:warnings=['Repository looks ready for normal work.']
        self.alerts.delete('1.0','end');self.alerts.insert('1.0','\n'.join('• '+x for x in warnings))
        r=self.git.execute('log','-12','--date=short','--pretty=format:%h  %ad  %an  %s',check=False);self.recent.delete('1.0','end');self.recent.insert('1.0',r.output)
