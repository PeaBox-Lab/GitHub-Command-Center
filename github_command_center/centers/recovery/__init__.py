RECOVERY_CENTERS=("ReflogRecoveryCenter","DanglingObjectRecoveryCenter","LostFoundCenter","DetachedHeadRecoveryCenter","BackupBranchManager","RecoveryDashboardV2")
__all__=["RECOVERY_CENTERS","RecoveryDashboardV2"]
def __getattr__(name):
    if name=="RecoveryDashboardV2":
        from .dashboard import RecoveryDashboardV2
        return RecoveryDashboardV2
    raise AttributeError(name)
