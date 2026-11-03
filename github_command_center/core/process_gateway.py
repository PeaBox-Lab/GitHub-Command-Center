"""Process execution boundary for non-Git tools and byte-oriented Git commands."""
from __future__ import annotations
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

@dataclass(frozen=True)
class ProcessResult:
    args: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    stdout_bytes: bytes = b""
    stderr_bytes: bytes = b""
    @property
    def output(self):
        return (self.stdout + ("\n" if self.stdout and self.stderr else "") + self.stderr).strip()

def run_process(args: Sequence[str], *, cwd: str | Path | None = None, timeout: int = 600,
                env: Mapping[str, str] | None = None, input_text: str | None = None,
                input_bytes: bytes | None = None, binary: bool = False) -> ProcessResult:
    command=tuple(map(str,args))
    if binary:
        p=subprocess.run(command,cwd=cwd,input=input_bytes,capture_output=True,timeout=timeout,env=env)
        return ProcessResult(command,p.returncode,stdout_bytes=p.stdout,stderr_bytes=p.stderr)
    p=subprocess.run(command,cwd=cwd,input=input_text,text=True,capture_output=True,timeout=timeout,env=env,
                     encoding="utf-8",errors="replace")
    return ProcessResult(command,p.returncode,p.stdout,p.stderr)

def start_process(args: Sequence[str], *, cwd: str | Path | None = None, env: Mapping[str,str] | None = None,
                  merge_stderr: bool = False):
    return subprocess.Popen(tuple(map(str,args)),cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
                            encoding="utf-8",errors="replace")
