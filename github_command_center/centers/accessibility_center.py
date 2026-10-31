from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from ..services import PreferencesService
from ..ui.accessibility import AccessibilityPreferences,apply_accessible_style,set_text_scale

class AccessibilityCenter(tk.Toplevel):
    def __init__(self,parent,repo=None):
        super().__init__(parent);self.title("Accessibility & Display");self.geometry("760x560");self.store=PreferencesService();self._build();self.load()
    def _build(self):
        f=ttk.Frame(self,padding=18);f.pack(fill="both",expand=True);self.high=tk.BooleanVar();self.large=tk.BooleanVar();self.motion=tk.BooleanVar();self.focus=tk.BooleanVar(value=True)
        ttk.Label(f,text="Accessibility & Display",font=("Segoe UI Semibold",16)).pack(anchor="w",pady=(0,12))
        ttk.Checkbutton(f,text="High contrast",variable=self.high).pack(anchor="w",pady=5)
        ttk.Checkbutton(f,text="Large text and larger row targets",variable=self.large).pack(anchor="w",pady=5)
        ttk.Checkbutton(f,text="Reduce motion / indeterminate animations",variable=self.motion).pack(anchor="w",pady=5)
        ttk.Checkbutton(f,text="Enhanced keyboard focus indicators",variable=self.focus).pack(anchor="w",pady=5)
        ttk.Separator(f).pack(fill="x",pady=14)
        ttk.Label(f,text="Keyboard access",font=("Segoe UI Semibold",11)).pack(anchor="w")
        ttk.Label(f,text="Ctrl+K  Command Palette\nTab / Shift+Tab  Move focus\nEnter / Space  Activate focused controls\nF5  Refresh active repository view\nEsc  Close dialogs where supported",justify="left").pack(anchor="w",pady=8)
        bar=ttk.Frame(f);bar.pack(fill="x",pady=12);ttk.Button(bar,text="Apply now",command=self.apply,style="Accessible.TButton").pack(side="right");ttk.Button(bar,text="Reset defaults",command=self.reset).pack(side="right",padx=6)
    def load(self):
        p=self.store.load();self.high.set(bool(p.get("high_contrast",False)));self.large.set(bool(p.get("large_text",False)));self.motion.set(bool(p.get("reduce_motion",False)));self.focus.set(bool(p.get("focus_indicators",True)));self.apply(save=False)
    def prefs(self):return AccessibilityPreferences(self.high.get(),self.large.get(),self.motion.get(),self.focus.get())
    def apply(self,save=True):
        p=self.prefs();apply_accessible_style(self,p);set_text_scale(self,p.large_text)
        if save:
            current=self.store.load();current.update({"high_contrast":p.high_contrast,"large_text":p.large_text,"reduce_motion":p.reduce_motion,"focus_indicators":p.focus_indicators});self.store.save(current)
    def reset(self):self.high.set(False);self.large.set(False);self.motion.set(False);self.focus.set(True);self.apply()
