"""Shared UI package.

Imports stay lazy so non-GUI model/navigation tests can run on headless Python
installations where tkinter is not available.
"""
__all__=["JobPanel","apply_modern_style"]

def __getattr__(name):
    if name=="JobPanel":
        from .job_panel import JobPanel
        return JobPanel
    if name=="apply_modern_style":
        from .styles import apply_modern_style
        return apply_modern_style
    raise AttributeError(name)
