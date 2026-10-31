RELEASE_CENTERS=("ReleaseCenter","ReleaseCompareCenter","ReleaseEvidenceCenter","ReleaseAssetIntegrityCenter","LocalReleaseArchiveCenter","ReleaseEvidenceV2")
__all__=["RELEASE_CENTERS","ReleaseEvidenceV2","ReleasePublishCenterV2"]
def __getattr__(name):
    if name=="ReleaseEvidenceV2":
        from .evidence import ReleaseEvidenceV2
        return ReleaseEvidenceV2
    if name=="ReleasePublishCenterV2":
        from .publish_center import ReleasePublishCenterV2
        return ReleasePublishCenterV2
    raise AttributeError(name)
