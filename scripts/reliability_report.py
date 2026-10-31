from __future__ import annotations
import json,platform,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(args):
 start=time.perf_counter();p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace");return {"args":args,"returncode":p.returncode,"seconds":round(time.perf_counter()-start,4),"stdout":p.stdout[-5000:],"stderr":p.stderr[-5000:]}

def main():
 report={"python":sys.version,"platform":platform.platform(),"checks":[run([sys.executable,"-m","compileall","-q","."]),run([sys.executable,"-m","unittest","discover","-s","tests","-v"])]}
 target=ROOT/"reliability-report.json";target.write_text(json.dumps(report,indent=2),encoding="utf-8");print(target);return 0 if all(x["returncode"]==0 for x in report["checks"]) else 1
if __name__=="__main__":raise SystemExit(main())
