RELEASE_CENTERS=("ReleaseCenter","ReleaseCompareCenter","ReleaseEvidenceCenter","ReleaseAssetIntegrityCenter","LocalReleaseArchiveCenter","ReleaseEvidenceV2")
__all__=["RELEASE_CENTERS","ReleaseEvidenceV2"]
def __getattr__(name):
    if name=="ReleaseEvidenceV2":
        from .evidence import ReleaseEvidenceV2
        return ReleaseEvidenceV2
    raise AttributeError(name)
