from __future__ import annotations
import json,os,platform,tkinter as tk
from pathlib import Path
from tkinter import ttk
ROOT=Path(__file__).resolve().parents[1]

def inspect_tree(root):
    errors=[];trees=[]
    def walk(w):
        if isinstance(w,ttk.Treeview):
            columns=list(w['columns']);widths=[int(w.column(c,'width')) for c in columns];trees.append({'columns':columns,'widths':widths,'rows':len(w.get_children(''))})
            if any(x<60 for x in widths):errors.append(f'narrow column: {widths}')
            for iid in w.get_children(''):
                for value in w.item(iid,'values'):
                    if '\n' in str(value) or '\r' in str(value):errors.append('multiline tree cell')
        for child in w.winfo_children():walk(child)
    walk(root);return trees,errors

def main():
    root=tk.Tk();root.withdraw();frame=ttk.Frame(root);frame.pack(fill='both',expand=True);tree=ttk.Treeview(frame,columns=('state','file','message'),show='headings');
    for c,w in (('state',90),('file',240),('message',420)):tree.heading(c,text=c.title());tree.column(c,width=w)
    tree.pack(fill='both',expand=True);tree.insert('', 'end', values=('OK','very/long/path/example.py','Completed successfully.\nNo replacement of adjacent cell text.'));root.update_idletasks();trees,errors=inspect_tree(root);report={'platform':platform.platform(),'tk':tk.TkVersion,'dpi_scaling':float(root.tk.call('tk','scaling')),'trees':trees,'errors':errors,'passed':not errors};(ROOT/'ui-regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8');root.destroy();print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
