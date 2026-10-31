from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
VERSION = '3.47.0'


def run(args):
    subprocess.run(args, cwd=ROOT, check=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    DIST.mkdir(exist_ok=True)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    run([sys.executable, '-m', 'compileall', '-q', '.'])
    run([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'packaging/github-command-center.spec'])
    exe = DIST / 'GitHubCommandCenter.exe'
    if not exe.exists():
        raise SystemExit(f'Missing packaged executable: {exe}')
    portable = DIST / f'GitHubCommandCenter-{VERSION}-portable.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(exe, exe.name)
        for name in ('README.md','CHANGELOG.md','RELEASE_NOTES.md','USER_GUIDE.md'):
            archive.write(ROOT / name, name)
    assets = [exe, portable]
    setup = DIST / 'installer' / f'GitHubCommandCenterSetup-{VERSION}.exe'
    if setup.exists(): assets.append(setup)
    sums = DIST / 'SHA256SUMS.txt'
    sums.write_text('\n'.join(f'{sha256(p)}  {p.name}' for p in assets) + '\n', encoding='utf-8')
    print('\n'.join(str(p) for p in [*assets, sums]))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
