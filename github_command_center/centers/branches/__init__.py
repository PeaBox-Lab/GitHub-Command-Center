BRANCH_CENTERS=("LocalBranchDashboard","RemoteBranchCenter","BranchRenamePlanner","SafeDeleteBranchWizard","UpstreamHealthCenter","BranchDashboardV2")
__all__=["BRANCH_CENTERS","BranchDashboardV2"]
def __getattr__(name):
    if name=="BranchDashboardV2":
        from .dashboard import BranchDashboardV2
        return BranchDashboardV2
    raise AttributeError(name)
