from __future__ import annotations
import subprocess

def run_process(args, **kwargs):
    return subprocess.run(args, **kwargs)

def start_process(args, **kwargs):
    return subprocess.Popen(args, **kwargs)
