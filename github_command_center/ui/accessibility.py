from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from .accessibility_model import AccessibilityPreferences, accessible_palette

def apply_accessible_style(widget, prefs: AccessibilityPreferences):
    p=accessible_palette(prefs.high_contrast);style=ttk.Style(widget);size=11 if prefs.large_text else 9
    style.configure('TLabel',font=('Segoe UI',size),foreground=p['fg'],background=p['bg'])
    style.configure('TButton',font=('Segoe UI',size),padding=(12,9) if prefs.large_text else (10,7))
    style.configure('Treeview',font=('Segoe UI',size),rowheight=34 if prefs.large_text else 29,background=p['bg'],fieldbackground=p['bg'],foreground=p['fg'])
    style.configure('Treeview.Heading',font=('Segoe UI Semibold',size),background=p['panel'],foreground=p['fg'])
    style.map('Treeview',background=[('selected',p['selection'])],foreground=[('selected','#000000' if prefs.high_contrast else p['fg'])])
    if prefs.focus_indicators:style.configure('Accessible.TButton',font=('Segoe UI Semibold',size),padding=(12,9),borderwidth=3,relief='solid')
    return style

def bind_keyboard_activation(widget,command):
    widget.bind('<Return>',lambda _e:command(),add='+');widget.bind('<space>',lambda _e:command(),add='+')

def set_text_scale(root,large:bool):root.tk.call('tk','scaling',1.35 if large else 1.0)
