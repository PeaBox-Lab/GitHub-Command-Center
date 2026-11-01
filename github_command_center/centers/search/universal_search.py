from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import GitService
from ...ui.simple_navigation import SIMPLE_MENU

class UniversalSearchCenter(tk.Toplevel):
    def __init__(self,parent,repo,open_tool=None):
        super().__init__(parent);self.repo=repo;self.git=GitService(repo);self.open_tool=open_tool;self.query=tk.StringVar();self.title('Search');self.geometry('980x680');self._build();self.search()
    def _build(self):
        top=ttk.Frame(self,padding=10);top.pack(fill='x');e=ttk.Entry(top,textvariable=self.query);e.pack(side='left',fill='x',expand=True);e.bind('<Return>',lambda _e:self.search());ttk.Button(top,text='Search',command=self.search).pack(side='left',padx=4)
        self.list=tk.Listbox(self,font=('Segoe UI',10));self.list.pack(fill='both',expand=True,padx=10,pady=5);self.list.bind('<Double-1>',lambda _e:self.activate());ttk.Button(self,text='Open selected',command=self.activate).pack(anchor='e',padx=10,pady=8);e.focus_set()
    def search(self):
        q=self.query.get().strip().lower();self.rows=[];self.list.delete(0,'end')
        for group in SIMPLE_MENU:
            for item in (group.primary,*group.secondary):
                hay=f'{group.name} {item.label} {item.destination} {item.hint}'.lower()
                if not q or q in hay:self.rows.append(('tool',item.destination));self.list.insert('end',f'Tool  |  {group.name}  |  {item.label}  —  {item.hint}')
        if len(q)>=2:
            for kind,args in [('branch',('for-each-ref','--format=%(refname:short)','refs/heads/')),('tag',('tag','--list',f'*{q}*')),('commit',('log','--all','-30','--oneline','--regexp-ignore-case','--grep',q))]:
                for value in self.git.execute(*args,check=False).stdout.splitlines():
                    if q in value.lower() or kind=='commit':self.rows.append((kind,value));self.list.insert('end',f'{kind.title()}  |  {value}')
    def activate(self):
        s=self.list.curselection()
        if not s:return
        kind,value=self.rows[s[0]]
        if kind=='tool' and self.open_tool:self.open_tool(value)
