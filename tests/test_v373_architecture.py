import ast
from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_shell_is_focused():
    path=ROOT/'github_command_center/local_git_gui.py'; text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
    assert len(text.splitlines()) < 300
    assert [n.name for n in tree.body if isinstance(n,ast.ClassDef)] == ['LocalGitWindow']

def test_feature_domains_are_bounded_and_parse():
    paths=sorted((ROOT/'github_command_center/features').glob('*_tools.py'))
    assert len(paths)==3
    for path in paths:
        text=path.read_text(encoding='utf-8'); ast.parse(text); assert len(text.splitlines()) < 1800

def test_command_gateway_is_shared():
    gateway=(ROOT/'github_command_center/core/command_gateway.py').read_text(encoding='utf-8')
    assert 'GitService' in gateway
    for path in (ROOT/'github_command_center/features').glob('*_tools.py'):
        assert 'from ..core.command_gateway import GitError, git' in path.read_text(encoding='utf-8')

def test_compatibility_exports_remain():
    text=(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8')
    for name in ('CommandPalette','CommitGraphWindow','StashManagerPro','WorktreeMoveCenter','GitCheckIgnoreBatchCenter'):
        assert name in text or '_feature_symbols' in text
