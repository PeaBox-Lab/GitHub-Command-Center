from __future__ import annotations
import tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox,simpledialog,ttk
from ...services import GitService,JobService
from ...ui import JobPanel
from ...ui.table_layout import ensure_horizontal_scrollbar

class GitLogVisualizerCenter(tk.Toplevel):
    """Searchable branch-aware graphical Git log with commit inspection and comparisons."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.rows=[]
        self.title('Git Log Visualizer');self.geometry('1320x820');self.limit=tk.IntVar(value=500);self.query=tk.StringVar();self.refs=tk.StringVar(value='--all');self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x');ttk.Label(bar,text='Refs').pack(side='left');ttk.Entry(bar,textvariable=self.refs,width=20).pack(side='left',padx=3);ttk.Label(bar,text='Search').pack(side='left');ttk.Entry(bar,textvariable=self.query).pack(side='left',fill='x',expand=True,padx=3);ttk.Label(bar,text='Limit').pack(side='left');ttk.Spinbox(bar,from_=50,to=5000,increment=50,textvariable=self.limit,width=7).pack(side='left');ttk.Button(bar,text='Refresh',command=self.refresh,style='Accent.TButton').pack(side='left',padx=4);ttk.Button(bar,text='Compare selected to HEAD',command=self.compare).pack(side='left')
        pane=ttk.Panedwindow(self,orient='vertical');pane.pack(fill='both',expand=True,padx=8,pady=5);top=ttk.Frame(pane);bottom=ttk.Frame(pane);pane.add(top,weight=3);pane.add(bottom,weight=2)
        self.tree=ttk.Treeview(top,columns=('graph','hash','date','author','refs','subject'),show='headings')
        for c,t,w in (('graph','Graph',170),('hash','Commit',95),('date','Date',110),('author','Author',170),('refs','Refs',270),('subject','Subject',500)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True);ensure_horizontal_scrollbar(self.tree,top);self.tree.bind('<<TreeviewSelect>>',lambda e:self.inspect())
        self.out=tk.Text(bottom,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True)
    def refresh(self):
        args=['log',f'-{int(self.limit.get())}','--graph','--date=short','--decorate=short','--pretty=format:%x1f%H%x1f%h%x1f%ad%x1f%an%x1f%D%x1f%s']
        ref=self.refs.get().strip()
        if ref:args += ref.split()
        if self.query.get().strip():args += ['--regexp-ignore-case','--grep',self.query.get().strip()]
        raw=self.git.execute(*args,check=False).stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if '\x1f' not in line:continue
            graph,rest=line.split('\x1f',1);p=rest.split('\x1f',5)
            if len(p)==6:
                row=(graph,p[0],p[1],p[2],p[3],p[4],p[5]);self.rows.append(row);self.tree.insert('','end',iid=str(len(self.rows)-1),values=(graph,p[1],p[2],p[3],p[4],p[5]))
    def selected(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def inspect(self):
        r=self.selected()
        if not r:return
        v=self.git.execute('show','--stat','--patch','--find-renames',r[1],check=False).output;self.out.delete('1.0','end');self.out.insert('1.0',v)
    def compare(self):
        r=self.selected()
        if not r:return
        v=self.git.execute('log','--left-right','--graph','--oneline',f'{r[1]}...HEAD',check=False).output+'\n\n'+self.git.execute('diff','--stat',r[1],'HEAD',check=False).output;self.out.delete('1.0','end');self.out.insert('1.0',v)

class StashWorkbenchCenter(tk.Toplevel):
    """Full stash lifecycle with preview, create/apply/pop/branch/drop and selected-path stash."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.jobs=JobService();self.rows=[];self.message=tk.StringVar(value='Work in progress');self.include_untracked=tk.BooleanVar(value=True);self.keep_index=tk.BooleanVar();self.title('Stash Workbench');self.geometry('1200x780');self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x');ttk.Entry(bar,textvariable=self.message).pack(side='left',fill='x',expand=True);ttk.Checkbutton(bar,text='Include untracked',variable=self.include_untracked).pack(side='left',padx=4);ttk.Checkbutton(bar,text='Keep index',variable=self.keep_index).pack(side='left');ttk.Button(bar,text='Create stash',command=self.create,style='Accent.TButton').pack(side='left',padx=4);ttk.Button(bar,text='Selected paths',command=self.selective).pack(side='left');ttk.Button(bar,text='Refresh',command=self.refresh).pack(side='left',padx=3)
        pane=ttk.Panedwindow(self,orient='vertical');pane.pack(fill='both',expand=True,padx=8,pady=5);top=ttk.Frame(pane);bottom=ttk.Frame(pane);pane.add(top,weight=3);pane.add(bottom,weight=2)
        self.tree=ttk.Treeview(top,columns=('stash','date','subject'),show='headings')
        for c,t,w in (('stash','Stash',110),('date','Date',190),('subject','Context / message',760)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True);ensure_horizontal_scrollbar(self.tree,top);self.tree.bind('<<TreeviewSelect>>',lambda e:self.preview())
        actions=ttk.Frame(bottom);actions.pack(fill='x');
        for text,cmd in (('Apply',self.apply),('Pop',self.pop),('Create branch',self.branch),('Drop',self.drop)):ttk.Button(actions,text=text,command=cmd).pack(side='left',padx=2,pady=3)
        self.out=tk.Text(bottom,wrap='none',font=('Consolas',9),bg='#0f172a',fg='#e2e8f0');self.out.pack(fill='both',expand=True);self.panel=JobPanel(self,self.jobs);self.panel.pack(fill='both',expand=True,padx=8,pady=5)
    def current(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def refresh(self):
        raw=self.git.execute('stash','list','--date=iso-strict','--format=%gd%x1f%cd%x1f%gs',check=False).stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for l in raw.splitlines():
            p=l.split('\x1f',2)
            if len(p)==3:self.rows.append(p);self.tree.insert('','end',iid=str(len(self.rows)-1),values=p)
    def preview(self):
        s=self.current()
        if s:self.out.delete('1.0','end');self.out.insert('1.0',self.git.execute('stash','show','--stat','--patch',s,check=False).output)
    def create(self):
        args=['git','stash','push','-m',self.message.get().strip() or 'Work in progress']
        if self.include_untracked.get():args.append('--include-untracked')
        if self.keep_index.get():args.append('--keep-index')
        self.panel.start(args,self.repo)
    def selective(self):
        paths=simpledialog.askstring('Selective stash','Comma-separated repository-relative paths:',parent=self)
        if not paths:return
        selected=[x.strip() for x in paths.split(',') if x.strip()];args=['git','stash','push','-m',self.message.get().strip() or 'Selective stash','--',*selected];self.panel.start(args,self.repo)
    def apply(self):
        s=self.current()
        if s:self.panel.start(['git','stash','apply',s],self.repo)
    def pop(self):
        s=self.current()
        if s and messagebox.askyesno('Pop stash',f'Apply and drop {s}?',parent=self):self.panel.start(['git','stash','pop',s],self.repo)
    def branch(self):
        s=self.current()
        if not s:return
        name=simpledialog.askstring('Stash branch','New branch name:',parent=self)
        if name:self.panel.start(['git','stash','branch',name,s],self.repo)
    def drop(self):
        s=self.current()
        if s and messagebox.askyesno('Drop stash',f'Permanently drop {s}?',parent=self):self.panel.start(['git','stash','drop',s],self.repo)

class WorktreeWorkbenchCenter(tk.Toplevel):
    """Worktree inventory and lifecycle management with add/lock/unlock/move/remove/prune."""
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.jobs=JobService();self.rows=[];self.title('Worktree Workbench');self.geometry('1220x760');self._build();self.refresh()
    def _build(self):
        bar=ttk.Frame(self,padding=8);bar.pack(fill='x');
        for text,cmd in (('Add worktree',self.add),('Lock',self.lock),('Unlock',self.unlock),('Move',self.move),('Remove',self.remove),('Prune dry-run',self.preview_prune),('Prune',self.prune),('Refresh',self.refresh)):ttk.Button(bar,text=text,command=cmd).pack(side='left',padx=2)
        self.tree=ttk.Treeview(self,columns=('path','branch','head','locked','prunable'),show='headings')
        for c,t,w in (('path','Worktree',510),('branch','Branch',250),('head','HEAD',120),('locked','Locked',90),('prunable','Prunable',100)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True,padx=8,pady=5);ensure_horizontal_scrollbar(self.tree,self);self.panel=JobPanel(self,self.jobs);self.panel.pack(fill='both',expand=True,padx=8,pady=5)
    def refresh(self):
        raw=self.git.execute('worktree','list','--porcelain',check=False).stdout;self.rows=[];cur={};self.tree.delete(*self.tree.get_children())
        for l in raw.splitlines()+['']:
            if not l:
                if cur:self.rows.append(cur);cur={}
            elif ' ' in l:
                k,v=l.split(' ',1);cur[k]=v
            else:cur[l]='true'
        for i,r in enumerate(self.rows):self.tree.insert('','end',iid=str(i),values=(r.get('worktree',''),r.get('branch','').replace('refs/heads/',''),r.get('HEAD','')[:12],'Yes' if 'locked' in r else 'No','Yes' if 'prunable' in r else 'No'))
    def current(self):
        s=self.tree.selection();return self.rows[int(s[0])] if s else None
    def add(self):
        parent=filedialog.askdirectory(parent=self,title='Choose parent folder')
        if not parent:return
        branch=simpledialog.askstring('Worktree','Branch name:',parent=self)
        if not branch:return
        dest=str(Path(parent)/branch.replace('/','-'));exists=self.git.execute('show-ref','--verify',f'refs/heads/{branch}',check=False).ok;args=['git','worktree','add',dest,branch] if exists else ['git','worktree','add','-b',branch,dest];self.panel.start(args,self.repo)
    def _path_action(self,verb):
        r=self.current()
        if r:self.panel.start(['git','worktree',verb,r['worktree']],self.repo)
    def lock(self):self._path_action('lock')
    def unlock(self):self._path_action('unlock')
    def move(self):
        r=self.current()
        if not r:return
        dest=filedialog.askdirectory(parent=self,title='Choose new worktree location')
        if dest:self.panel.start(['git','worktree','move',r['worktree'],dest],self.repo)
    def remove(self):
        r=self.current()
        if not r:return
        if Path(r['worktree']).resolve()==Path(self.repo).resolve():return messagebox.showwarning('Worktree','The primary worktree cannot be removed here.',parent=self)
        if messagebox.askyesno('Remove worktree',f"Remove worktree?\n{r['worktree']}",parent=self):self.panel.start(['git','worktree','remove',r['worktree']],self.repo)
    def preview_prune(self):self.panel.start(['git','worktree','prune','--dry-run','--verbose'],self.repo)
    def prune(self):
        if messagebox.askyesno('Prune worktrees','Remove stale worktree metadata?',parent=self):self.panel.start(['git','worktree','prune','--verbose'],self.repo)

class CommitGraphFilterCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.rows=[];self.title('Interactive Commit Graph');self.geometry('1360x820');self.author=tk.StringVar();self.since=tk.StringVar();self.until=tk.StringVar();self.message=tk.StringVar();self.path=tk.StringVar();self.refs=tk.StringVar(value='--all');self.mode=tk.StringVar(value='All');self.first_parent=tk.BooleanVar();self._build();self.refresh()
    def _build(self):
        f=ttk.LabelFrame(self,text='Filters',padding=8);f.pack(fill='x',padx=8,pady=5)
        for i,(n,v) in enumerate((('Refs',self.refs),('Author',self.author),('Since',self.since),('Until',self.until),('Message',self.message),('Path',self.path))):ttk.Label(f,text=n).grid(row=0,column=i*2,sticky='w');ttk.Entry(f,textvariable=v,width=16).grid(row=0,column=i*2+1,padx=3)
        ttk.Combobox(f,textvariable=self.mode,values=('All','Merges only','No merges'),state='readonly',width=14).grid(row=1,column=1);ttk.Checkbutton(f,text='First parent',variable=self.first_parent).grid(row=1,column=2,columnspan=2);ttk.Button(f,text='Apply',command=self.refresh).grid(row=1,column=10);ttk.Button(f,text='Reset',command=self.reset).grid(row=1,column=11)
        p=ttk.Panedwindow(self,orient='vertical');p.pack(fill='both',expand=True,padx=8,pady=5);a=ttk.Frame(p);b=ttk.Frame(p);p.add(a,weight=3);p.add(b,weight=2)
        self.tree=ttk.Treeview(a,columns=('graph','hash','date','author','refs','subject'),show='headings')
        for c,t,w in (('graph','Graph',180),('hash','Commit',90),('date','Date',105),('author','Author',170),('refs','Refs',280),('subject','Subject',500)):self.tree.heading(c,text=t);self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True);ensure_horizontal_scrollbar(self.tree,a);self.tree.bind('<<TreeviewSelect>>',lambda e:self.inspect());self.out=tk.Text(b,wrap='none',font=('Consolas',9));self.out.pack(fill='both',expand=True)
    def reset(self):
        for v in (self.author,self.since,self.until,self.message,self.path):v.set('')
        self.refs.set('--all');self.mode.set('All');self.first_parent.set(False);self.refresh()
    def refresh(self):
        args=['log','-1000','--graph','--date=short','--decorate=short','--pretty=format:%x1f%H%x1f%h%x1f%ad%x1f%an%x1f%D%x1f%s']
        for flag,var in (('--author',self.author),('--since',self.since),('--until',self.until),('--grep',self.message)):
            if var.get().strip():args += [flag,var.get().strip()]
        if self.mode.get()=='Merges only':args.append('--merges')
        elif self.mode.get()=='No merges':args.append('--no-merges')
        if self.first_parent.get():args.append('--first-parent')
        if self.refs.get().strip():args += self.refs.get().split()
        if self.path.get().strip():args += ['--',self.path.get().strip()]
        raw=self.git.execute(*args,check=False).stdout;self.rows=[];self.tree.delete(*self.tree.get_children())
        for line in raw.splitlines():
            if '\x1f' not in line:continue
            graph,rest=line.split('\x1f',1);q=rest.split('\x1f',5)
            if len(q)==6:self.rows.append((graph,*q));self.tree.insert('','end',iid=str(len(self.rows)-1),values=(graph,q[1],q[2],q[3],q[4],q[5]))
    def inspect(self):
        s=self.tree.selection()
        if s:self.out.delete('1.0','end');self.out.insert('1.0',self.git.execute('show','--stat','--patch',self.rows[int(s[0])][1],check=False).output)

class StashConflictPreviewCenter(tk.Toplevel):
    def __init__(self,parent,repo):
        super().__init__(parent);self.git=GitService(repo);self.rows=[];self.title('Stash Diff & Conflict Preview');self.geometry('1250x800');self._build();self.refresh()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Button(b,text='Refresh',command=self.refresh).pack(side='left');ttk.Button(b,text='Patch',command=self.patch).pack(side='left');ttk.Button(b,text='Conflict preview',command=self.conflicts).pack(side='left');self.tree=ttk.Treeview(self,columns=('stash','date','subject'),show='headings')
        for c,t,w in (('stash','Stash',120),('date','Date',190),('subject','Message',760)):self.tree.heading(c,text=t);self.tree.column(c,width=w)
        self.tree.pack(fill='x',padx=8);self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=8,pady=5);self.diff=tk.Text(self.tabs,wrap='none',font=('Consolas',9));self.risk=tk.Text(self.tabs,wrap='none',font=('Consolas',9));self.tabs.add(self.diff,text='Diff');self.tabs.add(self.risk,text='Conflict preview')
    def current(self):
        s=self.tree.selection();return self.rows[int(s[0])][0] if s else None
    def refresh(self):
        self.rows=[];self.tree.delete(*self.tree.get_children())
        for l in self.git.execute('stash','list','--date=iso-strict','--format=%gd%x1f%cd%x1f%gs',check=False).stdout.splitlines():
            p=l.split('\x1f',2)
            if len(p)==3:self.rows.append(p);self.tree.insert('','end',iid=str(len(self.rows)-1),values=p)
    def patch(self):
        s=self.current()
        if s:self.diff.delete('1.0','end');self.diff.insert('1.0',self.git.execute('stash','show','--stat','--patch',s,check=False).output);self.tabs.select(self.diff)
    def conflicts(self):
        s=self.current()
        if not s:return
        base=self.git.execute('rev-parse',f'{s}^1',check=False).stdout.strip();head=self.git.execute('rev-parse','HEAD',check=False).stdout.strip();stash=self.git.execute('rev-parse',s,check=False).stdout.strip();current=set(self.git.execute('diff','--name-only',base,head,check=False).stdout.splitlines());saved=set(self.git.execute('diff','--name-only',base,stash,check=False).stdout.splitlines());overlap=sorted(current & saved);tree=self.git.execute('merge-tree',base,head,stash,check=False).output;text='READ-ONLY PREVIEW\n\nPaths changed in both HEAD and stash:\n'+('\n'.join(overlap) or '(none)')+'\n\nMerge-tree output:\n'+tree;self.risk.delete('1.0','end');self.risk.insert('1.0',text);self.tabs.select(self.risk)

