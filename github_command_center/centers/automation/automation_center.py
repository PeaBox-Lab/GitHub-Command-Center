from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ...services import JobService
from ...ui import JobPanel

class AutomationCenter(tk.Toplevel):
    PRESETS={
      'Before commit':[['git','status','--short','--branch'],['python','-m','compileall','-q','.']],
      'Before push':[['git','status','--short','--branch'],['python','-m','unittest','discover','-s','tests','-v']],
      'Repository health':[['git','fsck','--no-progress'],['git','count-objects','-vH']],
      'Maintenance':[['git','maintenance','run','--auto']],
    }
    def __init__(self,parent,repo):
        super().__init__(parent);self.repo=repo;self.jobs=JobService();self.preset=tk.StringVar(value='Before push');self.title('Automation Center');self.geometry('1080x720');self._build()
    def _build(self):
        b=ttk.Frame(self,padding=8);b.pack(fill='x');ttk.Combobox(b,textvariable=self.preset,values=list(self.PRESETS),state='readonly',width=24).pack(side='left');ttk.Button(b,text='Run first step',command=self.run,style='Accent.TButton').pack(side='left',padx=4);ttk.Label(b,text='Safe preset workflows only. No arbitrary shell execution.').pack(side='right');self.panel=JobPanel(self,self.jobs);self.panel.pack(fill='both',expand=True,padx=8,pady=8)
    def run(self):
        steps=self.PRESETS[self.preset.get()]
        if steps:self.panel.start(steps[0],self.repo)
