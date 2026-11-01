from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from .simple_navigation import SIMPLE_MENU
from .workspace_state import WorkspaceStateService
class WorkspaceShell(tk.Toplevel):
    def __init__(self,parent,repo,registry):
        super().__init__(parent);self.repo=repo;self.registry=registry;self.store=WorkspaceStateService();self.state=self.store.load();self.title('GitHub Command Center Workspace');self.geometry(self.state.geometry);self.protocol('WM_DELETE_WINDOW',self.close);self._build();self.show_group('Changes')
    def _build(self):
        top=ttk.Frame(self,padding=10);top.pack(fill='x');ttk.Label(top,text='GitHub Command Center',font=('Segoe UI Semibold',15)).pack(side='left');ttk.Label(top,text=self.repo).pack(side='left',padx=12);ttk.Button(top,text='Search',command=lambda:self.open_tool('Universal Search')).pack(side='right');ttk.Button(top,text='Home',command=lambda:self.open_tool('Home Dashboard')).pack(side='right',padx=4)
        body=ttk.Panedwindow(self,orient='horizontal');body.pack(fill='both',expand=True);left=ttk.Frame(body,padding=8);right=ttk.Frame(body,padding=14);body.add(left,weight=1);body.add(right,weight=4)
        self.groups=tk.Listbox(left,font=('Segoe UI',10),exportselection=False);self.groups.pack(fill='both',expand=True)
        for g in SIMPLE_MENU:self.groups.insert('end',g.name)
        self.groups.bind('<<ListboxSelect>>',lambda _e:self._selected())
        self.heading=tk.StringVar();self.desc=tk.StringVar();ttk.Label(right,textvariable=self.heading,font=('Segoe UI Semibold',18)).pack(anchor='w');ttk.Label(right,textvariable=self.desc,wraplength=720).pack(anchor='w',pady=(4,14));self.cards=ttk.Frame(right);self.cards.pack(fill='x');ttk.Separator(right).pack(fill='x',pady=16)
        ttk.Label(right,text='Recent tools',font=('Segoe UI Semibold',11)).pack(anchor='w');self.recent=tk.Listbox(right,height=7);self.recent.pack(fill='x',pady=4);self.recent.bind('<Double-1>',lambda _e:self._open_list(self.recent));ttk.Label(right,text='Favorites',font=('Segoe UI Semibold',11)).pack(anchor='w',pady=(10,0));self.favs=tk.Listbox(right,height=6);self.favs.pack(fill='x',pady=4);self.favs.bind('<Double-1>',lambda _e:self._open_list(self.favs));self._refresh_lists()
    def _selected(self):
        s=self.groups.curselection()
        if s:self.show_group(SIMPLE_MENU[s[0]].name)
    def show_group(self,name):
        g=next(x for x in SIMPLE_MENU if x.name==name);self.heading.set(g.name);self.desc.set(g.description)
        for c in self.cards.winfo_children():c.destroy()
        for i,item in enumerate((g.primary,*g.secondary)):
            f=ttk.LabelFrame(self.cards,text=item.label,padding=10);f.grid(row=0,column=i,sticky='nsew',padx=4);self.cards.columnconfigure(i,weight=1);ttk.Label(f,text=item.hint,wraplength=220).pack(anchor='w',pady=(0,8));b=ttk.Frame(f);b.pack(fill='x');ttk.Button(b,text='Open',command=lambda n=item.destination:self.open_tool(n),style='Accent.TButton').pack(side='left');ttk.Button(b,text='Favorite',command=lambda n=item.destination:self.favorite(n)).pack(side='right')
    def open_tool(self,name):
        fn=self.registry.get(name)
        if fn:self.store.record_tool(self.state,name);self._refresh_lists();fn()
    def favorite(self,name):self.store.toggle_favorite(self.state,name);self._refresh_lists()
    def _refresh_lists(self):
        for box,items in ((self.recent,self.state.recent_tools),(self.favs,self.state.favorite_tools)):
            box.delete(0,'end')
            for x in items:box.insert('end',x)
    def _open_list(self,box):
        s=box.curselection()
        if s:self.open_tool(box.get(s[0]))
    def close(self):self.state.geometry=self.geometry();self.store.save(self.state);self.destroy()
