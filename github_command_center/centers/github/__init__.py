__all__=["AsyncGitHubCenter","AsyncGitHubWorkflowCenter"]
def __getattr__(name):
    if name=="AsyncGitHubCenter":
        from .async_github_center import AsyncGitHubCenter
        return AsyncGitHubCenter
    if name=="AsyncGitHubWorkflowCenter":
        from .workflow_center import AsyncGitHubWorkflowCenter
        return AsyncGitHubWorkflowCenter
    raise AttributeError(name)
