"""Recovery-domain center registry for staged migration.

The v3.43 release establishes explicit domain modules while the existing Tk
classes remain in the compatibility module. Future migrations move class bodies
here without changing command-palette behavior.
"""

RECOVERY_CENTERS = (
    "ReflogRecoveryCenter",
    "DanglingObjectRecoveryCenter",
    "LostFoundCenter",
    "DetachedHeadRecoveryCenter",
    "BackupBranchManager",
)
