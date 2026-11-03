from __future__ import annotations
from github_command_center.core.error_boundary import HANDLED_EXCEPTIONS, report_error

from tkinter import ttk


def configure_message_label(label: ttk.Label, minimum=240):
    """Keep long status/help labels inside their own region instead of covering adjacent controls."""
    try:
        label.configure(anchor="w", justify="left")
        label.bind("<Configure>", lambda e: label.configure(wraplength=max(minimum, e.width - 12)), add="+")
    except HANDLED_EXCEPTIONS:
        pass
    return label

