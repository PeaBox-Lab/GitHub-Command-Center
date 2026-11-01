from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--installer',required=True);p.add_argument('--installer-url',required=True);p.add_argument('--notes-url',default='');p.add_argument('--signature-url',default='');p.add_argument('--output',default='update-metadata.json');a=p.parse_args();path=Path(a.installer);h=hashlib.sha256(path.read_bytes()).hexdigest();Path(a.output).write_text(json.dumps({'version':a.version,'notes_url':a.notes_url,'installer_url':a.installer_url,'sha256':h,'signature_url':a.signature_url},indent=2),encoding='utf-8');print(a.output)
