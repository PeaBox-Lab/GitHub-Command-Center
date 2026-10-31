from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont, ttk

MIN_WIDTH = 72
DEFAULT_WIDTH = 140
MAX_WIDTH = 560
CELL_PADDING = 28


def display_text(value) -> str:
    """Convert arbitrary cell content to one safe Treeview line."""
    if value is None:
        return ""
    return " ".join(str(value).replace("\t", "    ").splitlines()).strip()


def normalize_tree_values(values):
    return tuple(display_text(value) for value in values)


def _font(widget):
    try:
        style = ttk.Style(widget)
        font_name = style.lookup("Treeview", "font") or "TkDefaultFont"
        return tkfont.nametofont(font_name)
    except Exception:
        return tkfont.nametofont("TkDefaultFont")


def measure(widget, value) -> int:
    try:
        return _font(widget).measure(display_text(value))
    except Exception:
        return len(display_text(value)) * 8


def desired_width(tree, column, value=None) -> int:
    heading = tree.heading(column, "text") or str(column)
    values = [heading]
    if value is not None:
        values.append(value)
    width = max(measure(tree, item) for item in values) + CELL_PADDING
    return max(MIN_WIDTH, min(width, MAX_WIDTH))


def ensure_horizontal_scrollbar(tree: ttk.Treeview):
    """Attach a horizontal bar below a packed Treeview without breaking existing layouts."""
    if getattr(tree, "_gccc_hscroll", None) is not None:
        return tree._gccc_hscroll
    parent = tree.master
    bar = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=bar.set)
    try:
        info = tree.pack_info()
        if info:
            bar.pack(fill="x", side="bottom", before=tree)
        else:
            bar.grid(row=999, column=0, sticky="ew")
    except Exception:
        return None
    tree._gccc_hscroll = bar
    return bar


def install_treeview_layout_guard():
    """Global compatibility fix for every existing Treeview in the app."""
    if getattr(ttk.Treeview, "_gccc_layout_guard", False):
        return

    original_insert = ttk.Treeview.insert
    original_heading = ttk.Treeview.heading

    def heading(self, column, option=None, **kw):
        result = original_heading(self, column, option, **kw)
        if kw.get("text") is not None:
            try:
                current = int(self.column(column, "width"))
                needed = desired_width(self, column)
                if current < needed:
                    self.column(column, width=needed, minwidth=MIN_WIDTH)
            except Exception:
                pass
        return result

    def insert(self, parent, index, iid=None, **kw):
        values = normalize_tree_values(kw.get("values", ()))
        if "values" in kw:
            kw["values"] = values
        result = original_insert(self, parent, index, iid=iid, **kw)
        try:
            columns = list(self["columns"])
            for pos, column in enumerate(columns):
                if pos >= len(values):
                    continue
                current = int(self.column(column, "width"))
                needed = desired_width(self, column, values[pos])
                if needed > current:
                    self.column(column, width=needed, minwidth=MIN_WIDTH, stretch=True)
            if sum(int(self.column(col, "width")) for col in columns) > max(self.winfo_width(), 700):
                ensure_horizontal_scrollbar(self)
        except Exception:
            pass
        return result

    ttk.Treeview.heading = heading
    ttk.Treeview.insert = insert
    ttk.Treeview._gccc_layout_guard = True
