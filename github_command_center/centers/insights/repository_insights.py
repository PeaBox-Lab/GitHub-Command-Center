from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import GitService

class RepositoryInsightsCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Repository Insights');self.geometry('1000x700');self._build();self.refresh()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Button(b,text='Refresh',command=self.refresh).pack(side='left');self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def safe(self,*a):return self.git.execute(*a,check=False).output
    def refresh(self):
        report='REPOSITORY INSIGHTS\n'+'='*72+'\n\nOBJECT STORAGE\n'+self.safe('count-objects','-vH')+'\n\nCONTRIBUTORS\n'+self.safe('shortlog','-sne','--all')+'\n\nSTALE LOCAL BRANCHES (>90 days indication by date)\n'+self.safe('for-each-ref','--sort=committerdate','--format=%(committerdate:short)  %(refname:short)  %(subject)','refs/heads/')+'\n\nTOP CHURN PATHS (recent 200 commits)\n'+self.safe('log','-200','--format=','--numstat')
        self.out.delete('1.0','end');self.out.insert('1.0',report)
