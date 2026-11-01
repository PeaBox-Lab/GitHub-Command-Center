from __future__ import annotations
import json,os,platform,subprocess,tempfile,tkinter as tk
from pathlib import Path
from tkinter import ttk
ROOT=Path(__file__).resolve().parents[1]

def make_repo():
    t=tempfile.TemporaryDirectory();p=Path(t.name);subprocess.run(["git","init","-q","-b","main"],cwd=p,check=True);subprocess.run(["git","config","user.name","UI Test"],cwd=p,check=True);subprocess.run(["git","config","user.email","ui@example.com"],cwd=p,check=True);(p/'README.md').write_text('hello\n');subprocess.run(["git","add","."],cwd=p,check=True);subprocess.run(["git","commit","-qm","initial"],cwd=p,check=True);(p/'README.md').write_text('changed\n');return t,p

def inspect(root):
    errors=[];tables=[]
    def walk(w):
        if isinstance(w,ttk.Treeview):
            widths=[int(w.column(c,'width')) for c in w['columns']];tables.append({'columns':list(w['columns']),'widths':widths,'rows':len(w.get_children(''))})
            if any(x<60 for x in widths):errors.append('column below 60px')
            for iid in w.get_children(''):
                if any('\n' in str(v) or '\r' in str(v) for v in w.item(iid,'values')):errors.append('multiline cell')
        for c in w.winfo_children():walk(c)
    walk(root);return tables,errors

def main():
    resolution=os.getenv('GCCC_TEST_RESOLUTION','1366x768');scale=int(os.getenv('GCCC_TEST_SCALING','100'))/100
    root=tk.Tk();root.withdraw();root.tk.call('tk','scaling',scale);tmp,repo=make_repo();created=[];errors=[]
    from github_command_center.centers.changes import ChangesCenterV2
    from github_command_center.centers.history import HistoryCenterV2
    from github_command_center.centers.review import ReviewCenterV2
    from github_command_center.centers.release import ReleaseEvidenceV2
    from github_command_center.centers.branches import BranchDashboardV2
    from github_command_center.centers.recovery import RecoveryDashboardV2
    for cls in (ChangesCenterV2,HistoryCenterV2,ReviewCenterV2,ReleaseEvidenceV2,BranchDashboardV2,RecoveryDashboardV2):
        try:w=cls(root,str(repo));w.update_idletasks();created.append(cls.__name__)
        except Exception as exc:errors.append(f'{cls.__name__}: {exc}')
    tables,layout_errors=inspect(root);errors.extend(layout_errors);report={'platform':platform.platform(),'resolution':resolution,'scaling':scale,'created':created,'tables':tables,'errors':errors,'passed':len(created)==6 and not errors};(ROOT/'ui-regression.json').write_text(json.dumps(report,indent=2),encoding='utf-8');root.destroy();tmp.cleanup();print(json.dumps(report,indent=2));return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
