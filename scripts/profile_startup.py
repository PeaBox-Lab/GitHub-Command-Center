from __future__ import annotations
import json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def timed(args):
    start=time.perf_counter();p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace",timeout=60)
    return {"args":args,"seconds":round(time.perf_counter()-start,6),"returncode":p.returncode,"stderr":p.stderr[-2000:]}

def main():
    checks=[timed([sys.executable,"-c","import github_command_center"]),timed([sys.executable,"-c","import github_command_center.services.git_service"]),timed([sys.executable,"-c","import github_command_center.services.diff_service"]),timed([sys.executable,"-c","import github_command_center.ui.navigation"])]
    report={"python":sys.version,"platform":platform.platform(),"cold_imports":checks,"budget_seconds":2.5,"passes_budget":all(x["returncode"]==0 and x["seconds"]<2.5 for x in checks)}
    path=ROOT/"startup-performance.json";path.write_text(json.dumps(report,indent=2),encoding="utf-8");print(json.dumps(report,indent=2));return 0 if report["passes_budget"] else 1
if __name__=="__main__":raise SystemExit(main())
