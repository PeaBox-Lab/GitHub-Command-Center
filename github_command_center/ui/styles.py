from __future__ import annotations
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk
from github_command_center.core.error_boundary import HANDLED_EXCEPTIONS, report_error

# Corporate color palette - professional light/dark themes
CORPORATE_PALETTES = {
    "light": {
        "bg": "#f8f9fa",
        "nav_bg": "#212529",
        "nav_fg": "#adb5bd",
        "card_bg": "#ffffff",
        "card_border": "#dee2e6",
        "text": "#212529",
        "muted": "#6c757d",
        "accent": "#2b5b84",
        "accent_active": "#1f466e",
        "success": "#27ae60",
        "warning": "#f39c12",
        "error": "#e74c3c",
    },
    "dark": {
        "bg": "#1a1d23",
        "nav_bg": "#16191f",
        "nav_fg": "#8a9ba8",
        "card_bg": "#212428",
        "card_border": "#30353d",
        "text": "#e0e0e0",
        "muted": "#667084",
        "accent": "#3b82f6",
        "accent_active": "#2563eb",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
    }
}


@dataclass
class ThemePreferences:
    mode: str = "light"  # "light" or "dark"
    last_used: str = "light"


class CorporateStyleManager:
    """Manages corporate-style theming with light/dark support."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.theme = ThemePreferences()
        self._palette = CORPORATE_PALETTES["light"]
        self._setup_themes()
        self._apply_theme()

    def _setup_themes(self):
        """Define both light and dark color schemes."""
        for palette_name in CORPORATE_PALETTES:
            palette = CORPORATE_PALETTES[palette_name]
            # Configure ttk styles for each palette
            ttk.Style().theme_use("clam")
            style = ttk.Style()
            style.theme_use("clam")
            style.configure(
                f"Corp.TButton",
                font=("Segoe UI", 10),
                padding=(10, 7),
                background=palette["bg"],
                foreground=palette["text"],
            )
            style.map(
                f"Corp.TButton",
                background=[("active", palette["accent_active"])],
            )
            style.configure(
                f"Corp.Accent.TButton",
                font=("Segoe UI Semibold", 10),
                padding=(10, 7),
                background=palette["accent"],
                foreground="white",
            )
            style.map(
                f"Corp.Accent.TButton",
                background=[("active", palette["accent_active"])],
            )
            style.configure(
                f"Corp.Treeview",
                font=("Segoe UI", 10),
                rowheight=32,
                background=palette["card_bg"],
                fieldbackground=palette["card_bg"],
                foreground=palette["text"],
            )
            style.configure(
                f"Corp.Treeview.Heading",
                font=("Segoe UI Semibold", 9),
                padding=8,
                background=palette["card_bg"],
                foreground=palette["muted"],
            )
            style.map(
                f"Corp.Treeview",
                background=[("selected", palette["accent"])],
                foreground=[("selected", "white")],
            )
            style.configure(
                f"Corp.TNotebook",
                background=palette["bg"],
                borderwidth=0,
            )
            style.configure(
                f"Corp.TNotebook.Tab",
                font=("Segoe UI", 9),
                padding=(10, 7),
                background=palette["bg"],
                foreground=palette["muted"],
            )

    def set_mode(self, mode: str):
        """Switch between light and dark themes."""
        if mode in CORPORATE_PALETTES:
            self.theme.mode = mode
            self._palette = CORPORATE_PALETTES[mode]
            self._apply_theme()

    def get_mode(self) -> str:
        return self.theme.mode

    def _apply_theme(self):
        """Apply the current theme palette to all UI elements."""
        p = self._palette

        # Root window background
        self.root.configure(bg=p["bg"])

        # Update all widget styles
        style = ttk.Style()
        style.theme_use("clam")

        # Configure base styles with current palette
        style.configure(
            "TButton",
            font=("Segoe UI", 10),
            padding=(10, 7),
            background=p["bg"],
            foreground=p["text"],
        )
        style.map(
            "TButton",
            background=[("active", p["accent_active"])],
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI Semibold", 10),
            padding=(10, 7),
            background=p["accent"],
            foreground="white",
        )
        style.map(
            "Accent.TButton",
            background=[("active", p["accent_active"])],
        )

        style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=34,
            background=p["card_bg"],
            fieldbackground=p["card_bg"],
            foreground=p["text"],
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI Semibold", 10),
            padding=8,
            background=p["card_bg"],
            foreground=p["muted"],
        )
        style.map(
            "Treeview",
            background=[("selected", p["accent"])],
            foreground=[("selected", "white")],
        )

        style.configure(
            "TNotebook",
            background=p["bg"],
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10),
            padding=(10, 7),
            background=p["bg"],
            foreground=p["muted"],
        )


def apply_modern_style(widget) -> ttk.Style:
    """Legacy compatibility function - applies modern corporate style to widget.

    This is kept for backward compatibility with existing code that calls
    apply_modern_style. It delegates to the CorporateStyleManager when available.
    """
    style = ttk.Style(widget)
    try: style.theme_use("clam")
    except Exception: pass
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
    style.configure("Treeview", font=("Segoe UI", 9), rowheight=32, background="white", fieldbackground="white", borderwidth=0)
    style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9), padding=8, background="#f1f5f9", foreground="#334155")
    style.map("Treeview", background=[("selected", "#e0e7ff")], foreground=[("selected", "#111827")])
    style.configure("TNotebook", background="white", borderwidth=0)
    style.configure("TNotebook.Tab", font=("Segoe UI", 9), padding=(10, 7))
    return style