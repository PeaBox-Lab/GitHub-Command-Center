from __future__ import annotations

from tkinter import ttk


def apply_modern_style(widget) -> ttk.Style:
    style = ttk.Style(widget)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TButton", font=("Segoe UI", 9), padding=(10, 7), background="#f8fafc")
    style.map("TButton", background=[("active", "#e5e7eb")])
    style.configure(
        "Accent.TButton",
        font=("Segoe UI Semibold", 9),
        padding=(11, 7),
        background="#4f46e5",
        foreground="white",
    )
    style.map("Accent.TButton", background=[("active", "#4338ca")])
    style.configure("Treeview", font=("Segoe UI", 9), rowheight=29, background="white", fieldbackground="white", borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), padding=8, background="#f1f5f9", foreground="#334155")
    style.map("Treeview", background=[("selected", "#e0e7ff")], foreground=[("selected", "#111827")])
    style.configure("TNotebook", background="white", borderwidth=0)
    style.configure("TNotebook.Tab", font=("Segoe UI", 9), padding=(10, 7))
    return style
