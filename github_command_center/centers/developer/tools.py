from __future__ import annotations
import tkinter as tk
from pathlib import Path
from tkinter import filedialog,ttk
from ...services import GitService

class DeveloperToolboxCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.title('Developer Toolbox');self.geometry('1120x740');self.ref=tk.StringVar(value='HEAD');self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x');ttk.Entry(bar,textvariable=self.ref,width=24).pack(side='left')
        for label,cmd in (('Refresh',self.refresh),('Changed files',self.changed),('Check whitespace',self.whitespace),('Show commit',self.show_commit),('Generate patch',self.patch),('Export patch',self.export_patch)):ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=2)
        self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def run(self,*a):return self.git.execute(*a,check=False).output
    def put(self,v):self.out.delete('1.0','end');self.out.insert('1.0',v)
    def refresh(self):self.put('DEVELOPER TOOLBOX\n'+'='*72+'\n'+self.run('status','--short','--branch')+'\n\n'+self.run('diff','--stat'))
    def changed(self):self.put(self.run('diff','--name-status',self.ref.get().strip() or 'HEAD'))
    def whitespace(self):self.put(self.run('diff','--check',self.ref.get().strip() or 'HEAD'))
    def show_commit(self):self.put(self.run('show','--stat','--format=fuller',self.ref.get().strip() or 'HEAD'))
    def patch(self):self.patch_text=self.run('format-patch','-1','--stdout',self.ref.get().strip() or 'HEAD');self.put(self.patch_text)
    def export_patch(self):
        self.patch();p=filedialog.asksaveasfilename(parent=self,defaultextension='.patch',initialfile='commit.patch')
        if p:Path(p).write_text(self.patch_text,encoding='utf-8')

class GitObjectQueryCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Git Object Query');self.geometry('1080x700');self.object=tk.StringVar(value='HEAD');self.path=tk.StringVar();self._build();self.inspect()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x');ttk.Entry(bar,textvariable=self.object,width=28).pack(side='left');ttk.Entry(bar,textvariable=self.path).pack(side='left',fill='x',expand=True,padx=4)
        for label,cmd in (('Inspect',self.inspect),('Tree',self.tree),('Path at object',self.path_at),('Verify object',self.verify)):ttk.Button(bar,text=label,command=cmd).pack(side='left',padx=2)
        self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def run(self,*a):return self.git.execute(*a,check=False).output
    def put(self,v):self.out.delete('1.0','end');self.out.insert('1.0',v)
    def inspect(self):
        o=self.object.get().strip() or 'HEAD';self.put('TYPE: '+self.run('cat-file','-t',o)+'\nSIZE: '+self.run('cat-file','-s',o)+'\n\n'+self.run('cat-file','-p',o))
    def tree(self):self.put(self.run('ls-tree','-r','--long',self.object.get().strip() or 'HEAD'))
    def path_at(self):
        o=self.object.get().strip() or 'HEAD';p=self.path.get().strip();self.put(self.run('show',f'{o}:{p}') if p else 'Enter a repository-relative path.')
    def verify(self):self.put(self.run('rev-parse','--verify',self.object.get().strip() or 'HEAD')+'\n'+self.run('name-rev','--name-only',self.object.get().strip() or 'HEAD'))
