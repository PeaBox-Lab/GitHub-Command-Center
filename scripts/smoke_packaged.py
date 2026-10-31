from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def main(argv=None):
    root = Path((argv or sys.argv)[1]).resolve()
    exe = root / 'GitHubCommandCenter.exe'
    if not exe.exists() or exe.stat().st_size < 1024:
        raise SystemExit('Packaged EXE missing or unexpectedly small.')
    portable = next(root.glob('GitHubCommandCenter-*-portable.zip'), None)
    if not portable:
        raise SystemExit('Portable ZIP missing.')
    sums = root / 'SHA256SUMS.txt'
    if not sums.exists():
        raise SystemExit('SHA256SUMS.txt missing.')
    manifest = sums.read_text(encoding='utf-8')
    for path in (exe, portable):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if f'{digest}  {path.name}' not in manifest:
            raise SystemExit(f'Checksum mismatch: {path.name}')
    print('packaged smoke test passed')

if __name__ == '__main__':main()
