__all__=["ReviewCenterV2"]
def __getattr__(name):
    if name=="ReviewCenterV2":
        from .review_center import ReviewCenterV2
        return ReviewCenterV2
    raise AttributeError(name)
