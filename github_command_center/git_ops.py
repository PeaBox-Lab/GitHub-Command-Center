
import shutil
import subprocess
from pathlib import Path


class GitOperationError(RuntimeError):
    pass


def git_available():
    return shutil.which("git") is not None


def run_git(args, cwd=None):
    try:
        result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError as exc:
        raise GitOperationError("Git is not installed or is not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitOperationError("Git operation timed out.") from exc
    output = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode:
        raise GitOperationError(output or "Git operation failed.")
    return output or "Completed successfully."


def clone_repo(clone_url, workspace):
    workspace = Path(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    return run_git(["clone", clone_url], cwd=workspace)


def pull_repo(folder):
    return run_git(["pull", "--ff-only"], cwd=folder)


def status_repo(folder):
    return run_git(["status", "--short", "--branch"], cwd=folder)
