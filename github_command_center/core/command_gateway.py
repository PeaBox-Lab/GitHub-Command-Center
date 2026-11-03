from ..services import GitService
class GitError(RuntimeError): pass
def git(cwd,*args):
 try:return GitService(cwd).text(*map(str,args),timeout=900)
 except FileNotFoundError as exc:raise GitError("Git is not installed or not on PATH.") from exc
 except (OSError,ValueError,RuntimeError) as exc:raise GitError(str(exc)) from exc
