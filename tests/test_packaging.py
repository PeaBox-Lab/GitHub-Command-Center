import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class PackagingTests(unittest.TestCase):
 def test_spec_exists(self):self.assertTrue((ROOT/'packaging/github-command-center.spec').exists())
 def test_installer_exists(self):self.assertTrue((ROOT/'packaging/installer.iss').exists())
 def test_build_script_parses(self):ast.parse((ROOT/'scripts/build_release.py').read_text(encoding='utf-8'))
 def test_smoke_script_parses(self):ast.parse((ROOT/'scripts/smoke_packaged.py').read_text(encoding='utf-8'))
 def test_installer_version(self):self.assertIn('3.47.0',(ROOT/'packaging/installer.iss').read_text(encoding='utf-8'))
