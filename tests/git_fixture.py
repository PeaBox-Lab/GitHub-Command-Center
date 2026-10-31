from __future__ import annotations
import subprocess,tempfile
from pathlib import Path

class GitFixture:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
        self.run("init","-q","-b","main");self.run("config","user.name","Reliability Test");self.run("config","user.email","reliability@example.com")
    def run(self,*args,check=True):return subprocess.run(["git",*args],cwd=self.path,text=True,capture_output=True,check=check)
    def write(self,name,text):p=self.path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding="utf-8");return p
    def commit(self,message="commit"):
        self.run("add",".");self.run("commit","-q","-m",message);return self.run("rev-parse","HEAD").stdout.strip()
    def close(self):self.tmp.cleanup()
