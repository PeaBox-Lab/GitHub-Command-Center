from __future__ import annotations
import tkinter as tk
from pathlib import Path
from tkinter import filedialog,ttk
from ...services import GitService,JobService
from ...ui import JobPanel

class DevQualityCenter(tk.Toplevel):
    PRESETS={'Unit tests':['python','-m','unittest','discover','-s','tests','-v'],'Compile all':['python','-m','compileall','-q','.'],'Ruff':['ruff','check','github_command_center','tests'],'Bandit':['bandit','-q','-r','github_command_center','-x','tests'],'Pip audit':['pip-audit','-r','requirements.txt'],'Git whitespace':['git','diff','--check']}
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.jobs=JobService();self.title('Developer Quality');self.geometry('1120x740');self.action=tk.StringVar(value='Unit tests');self._build()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Combobox(b,textvariable=self.action,values=list(self.PRESETS),state='readonly',width=24).pack(side='left');ttk.Button(b,text='Run',command=self.run,style='Accent.TButton').pack(side='left',padx=4);self.panel=JobPanel(self,self.jobs);self.panel.pack(fill='both',expand=True,padx=8,pady=8)
    def run(self):
        j=self.jobs.jobs.get(self.panel.active_job_id) if self.panel.active_job_id else None
        if not j or j.status not in ('Queued','Running'):self.panel.start(self.PRESETS[self.action.get()],self.repo)

class CodeSearchCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Code Search');self.geometry('1120x720');self.query=tk.StringVar();self.path=tk.StringVar();self.history=tk.BooleanVar();self._build()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Entry(b,textvariable=self.query).pack(side='left',fill='x',expand=True);ttk.Entry(b,textvariable=self.path,width=24).pack(side='left',padx=4);ttk.Checkbutton(b,text='History',variable=self.history).pack(side='left');ttk.Button(b,text='Search',command=self.search,style='Accent.TButton').pack(side='left',padx=4);self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def search(self):
        q=self.query.get().strip();p=self.path.get().strip()
        if not q:return
        args=['log','--all','-G',q,'--oneline','--decorate','--stat'] if self.history.get() else ['grep','-n','-I','-i','-E',q]
        if p:args+=['--',p]
        r=self.git.execute(*args,check=False);self.out.delete('1.0','end');self.out.insert('1.0',r.output)

class PatchSeriesCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Patch Series');self.geometry('1080x700');self.range=tk.StringVar(value='HEAD~3..HEAD');self._build();self.preview()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Entry(b,textvariable=self.range).pack(side='left',fill='x',expand=True)
        for label,cmd in (('Preview',self.preview),('Export patches',self.export)):ttk.Button(b,text=label,command=cmd).pack(side='left',padx=3)
        self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def put(self,x):self.out.delete('1.0','end');self.out.insert('1.0',x)
    def preview(self):self.put(self.git.execute('log','--reverse','--oneline',self.range.get().strip(),check=False).output)
    def export(self):
        d=filedialog.askdirectory(parent=self)
        if d:self.put(self.git.execute('format-patch','-o',d,self.range.get().strip(),check=False).output)

class RepositoryMetricsCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Repository Metrics');self.geometry('1040x690');self._build();self.refresh()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Button(b,text='Refresh',command=self.refresh).pack(side='left');self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def refresh(self):
        files=self.git.lines('ls-files');types={}
        for f in files:types[Path(f).suffix.lower() or '(none)']=types.get(Path(f).suffix.lower() or '(none)',0)+1
        ext='\n'.join(f'{k:<15} {v:>6}' for k,v in sorted(types.items(),key=lambda x:-x[1])[:30]);commits=self.git.execute('rev-list','--count','HEAD',check=False).output;contributors=self.git.execute('shortlog','-sne','HEAD',check=False).output;objects=self.git.execute('count-objects','-vH',check=False).output
        self.out.delete('1.0','end');self.out.insert('1.0',f'REPOSITORY METRICS\n{"="*72}\nTracked files: {len(files)}\nCommits: {commits}\n\nTOP EXTENSIONS\n{ext}\n\nCONTRIBUTORS\n{contributors}\n\nOBJECTS\n{objects}')

class BuildCommandCenter(DevQualityCenter):
    pass

class DevArtifactCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.title('Developer Artifacts');self.geometry('1040x680');self.ref=tk.StringVar(value='HEAD');self._build()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Entry(b,textvariable=self.ref,width=24).pack(side='left');ttk.Button(b,text='Tree manifest',command=self.manifest).pack(side='left',padx=3);ttk.Button(b,text='Source ZIP',command=self.archive).pack(side='left');self.out=tk.Text(self,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True,padx=8,pady=5)
    def manifest(self):self.out.delete('1.0','end');self.out.insert('1.0',self.git.execute('ls-tree','-r','--full-tree',self.ref.get().strip() or 'HEAD',check=False).output)
    def archive(self):
        p=filedialog.asksaveasfilename(parent=self,defaultextension='.zip',initialfile='source.zip')
        if p:self.out.delete('1.0','end');self.out.insert('1.0',self.git.execute('archive','--format=zip',f'--output={p}',self.ref.get().strip() or 'HEAD',check=False).output+'\n'+p)
