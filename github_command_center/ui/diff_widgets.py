from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..services.diff_service import FileDiff


class SideBySideDiff(ttk.Frame):
    """Reusable synchronized two-pane diff renderer with word highlights."""

    COLORS = {
        "context": ("#f8fafc", "#f8fafc"),
        "delete": ("#fee2e2", "#ffffff"),
        "add": ("#ffffff", "#dcfce7"),
        "meta": ("#e2e8f0", "#e2e8f0"),
    }

    def __init__(self, master):
        super().__init__(master)
        self._syncing = False
        self._build()

    def _build(self):
        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text="Original", font=("Segoe UI Semibold", 10)).pack(side="left", expand=True)
        ttk.Label(header, text="Modified", font=("Segoe UI Semibold", 10)).pack(side="left", expand=True)
        panes = ttk.Panedwindow(self, orient="horizontal")
        panes.pack(fill="both", expand=True)
        self.left = tk.Text(panes, wrap="none", font=("Consolas", 9), bg="#ffffff", undo=False)
        self.right = tk.Text(panes, wrap="none", font=("Consolas", 9), bg="#ffffff", undo=False)
        panes.add(self.left, weight=1); panes.add(self.right, weight=1)
        for widget in (self.left, self.right):
            widget.tag_configure("delete", background="#fee2e2")
            widget.tag_configure("add", background="#dcfce7")
            widget.tag_configure("word_delete", background="#fca5a5")
            widget.tag_configure("word_add", background="#86efac")
            widget.tag_configure("line_number", foreground="#64748b")
            widget.configure(state="disabled")
        self.left.configure(yscrollcommand=lambda a, b: self._scroll(self.right, a, b))
        self.right.configure(yscrollcommand=lambda a, b: self._scroll(self.left, a, b))

    def _scroll(self, peer, first, last):
        if not self._syncing:
            self._syncing = True
            peer.yview_moveto(first)
            self._syncing = False

    def clear(self):
        for widget in (self.left, self.right):
            widget.configure(state="normal");widget.delete("1.0", "end");widget.configure(state="disabled")

    def render(self, file_diff: FileDiff):
        for widget in (self.left, self.right):widget.configure(state="normal");widget.delete("1.0", "end")
        if file_diff.binary:
            self.left.insert("end", "Binary file\n");self.right.insert("end", "Binary file\n")
        else:
            for hunk in file_diff.hunks:
                self.left.insert("end", hunk.header + "\n", "line_number");self.right.insert("end", hunk.header + "\n", "line_number")
                index = 0
                while index < len(hunk.lines):
                    line = hunk.lines[index]
                    if line.kind == "delete":
                        deleted=[];added=[]
                        while index<len(hunk.lines) and hunk.lines[index].kind=="delete":deleted.append(hunk.lines[index]);index+=1
                        while index<len(hunk.lines) and hunk.lines[index].kind=="add":added.append(hunk.lines[index]);index+=1
                        count=max(len(deleted),len(added))
                        for i in range(count):self._pair(deleted[i] if i<len(deleted) else None,added[i] if i<len(added) else None)
                        continue
                    if line.kind == "add":self._pair(None,line)
                    elif line.kind == "context":self._pair(line,line)
                    else:self._pair(line,line)
                    index+=1
        for widget in (self.left,self.right):widget.configure(state="disabled")

    def _pair(self, old, new):
        self._insert(self.left,old,"delete","word_delete",old.old_number if old else None)
        self._insert(self.right,new,"add","word_add",new.new_number if new else None)

    def _insert(self, widget, line, line_tag, word_tag, number):
        if line is None:widget.insert("end", "      \n");return
        widget.insert("end", f"{number if number is not None else '':>5} ", "line_number")
        if line.words:
            for kind,text in line.words:widget.insert("end",text,word_tag if kind in ("delete","add") else ())
        else:widget.insert("end",line.text,line_tag if line.kind in ("delete","add") else ())
        widget.insert("end","\n")
