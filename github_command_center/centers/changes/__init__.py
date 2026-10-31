__all__=["ChangesCenterV2"]
def __getattr__(name):
    if name=="ChangesCenterV2":
        from .changes_center import ChangesCenterV2
        return ChangesCenterV2
    raise AttributeError(name)
