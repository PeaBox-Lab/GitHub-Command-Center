from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_domains_have_no_direct_subprocess_calls():
 for p in (ROOT/'github_command_center/features/domains').glob('*.py'):
  s=p.read_text(encoding='utf-8'); assert 'subprocess.run(' not in s; assert 'subprocess.Popen(' not in s
def test_process_gateway_owns_process_execution():
 s=(ROOT/'github_command_center/core/process_gateway.py').read_text(encoding='utf-8'); assert 'subprocess.run(' in s; assert 'subprocess.Popen(' in s
def test_version_is_v380():
 assert '__version__ = "3.82.0"' in (ROOT/'github_command_center/__init__.py').read_text()
