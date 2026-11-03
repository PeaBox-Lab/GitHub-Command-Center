from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys, tempfile, tomllib, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from version_info import project_version
VERSION=project_version()
NAME=f'github_command_center_python_v{VERSION}'
EXCLUDES={'.git','.venv','.pytest_cache','__pycache__','build','dist','.coverage'}

def files_for_release():
    out=[]
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(part in EXCLUDES for part in rel.parts): continue
        if p.suffix in {'.pyc','.pyo'}: continue
        if rel.name.startswith(NAME): continue
        out.append(rel)
    return sorted(out,key=lambda p:p.as_posix())

def build_zip(output: Path):
    epoch=int(os.environ.get('SOURCE_DATE_EPOCH','1704067200'))
    import datetime
    dt=max(datetime.datetime(1980,1,1),datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).replace(tzinfo=None))
    zdt=(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for rel in files_for_release():
            info=zipfile.ZipInfo(rel.as_posix(),zdt);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,(ROOT/rel).read_bytes())

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default='dist');ap.add_argument('--evidence-dir',default='release-evidence');args=ap.parse_args()
    pyproject=tomllib.loads((ROOT/'pyproject.toml').read_text());pkg=(ROOT/'github_command_center/__init__.py').read_text()
    failures=[]
    if pyproject['project']['version']!=VERSION: failures.append('pyproject version mismatch')
    if f'__version__ = "{VERSION}"' not in pkg: failures.append('package version mismatch')
    outdir=ROOT/args.output_dir; evidence=ROOT/args.evidence_dir; shutil.rmtree(outdir,ignore_errors=True);outdir.mkdir();evidence.mkdir(exist_ok=True)
    archive=outdir/f'{NAME}.zip'; build_zip(archive)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest(); (outdir/f'{NAME}.sha256').write_text(f'{digest}  {archive.name}\n')
    with zipfile.ZipFile(archive) as z:
        bad=z.testzip(); names=z.namelist()
    if bad: failures.append(f'corrupt member: {bad}')
    if any(n.startswith('dist/') or n==archive.name for n in names): failures.append('release archive contains generated output')
    manifest=[{'path':p.as_posix(),'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in files_for_release()]
    (evidence/'file-manifest.json').write_text(json.dumps(manifest,indent=2))
    report={'version':VERSION,'archive':archive.name,'sha256':digest,'files':len(names),'self_inclusion':False,'zip_integrity':bad is None,'version_consistent':not failures,'passed':not failures,'failures':failures}
    (evidence/'packaging-gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return bool(failures)
if __name__=='__main__': raise SystemExit(main())
