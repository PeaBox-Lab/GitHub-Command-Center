from __future__ import annotations
import json,os,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(args,timeout=120):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace",timeout=timeout)
    return {"args":args,"returncode":p.returncode,"stdout":p.stdout[-3000:],"stderr":p.stderr[-3000:]}

def main():
    checks=[]
    checks.append(run([sys.executable,"-m","compileall","-q","."]))
    checks.append(run([sys.executable,"-m","unittest","discover","-s","tests","-v"]))
    checks.append(run(["git","--version"]))
    checks.append(run([sys.executable,"-c","import github_command_center; import github_command_center.services.git_service; import github_command_center.services.diff_service"]))
    env={"os":os.name,"platform":platform.platform(),"python":sys.version,"git":shutil.which("git"),"gh":shutil.which("gh"),"tkinter_check":"not-run"}
    tk=run([sys.executable,"-c","import tkinter; print(tkinter.TkVersion)"])
    env["tkinter_check"]="pass" if tk["returncode"]==0 else "fail"
    checks.append(tk)
    passed=all(x["returncode"]==0 for x in checks)
    report={"environment":env,"checks":checks,"passed":passed}
    (ROOT/"windows-validation.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2));return 0 if passed else 1
if __name__=="__main__":raise SystemExit(main())
