__all__=["HistoryCenterV2"]
def __getattr__(name):
    if name=="HistoryCenterV2":
        from .history_center import HistoryCenterV2
        return HistoryCenterV2
    raise AttributeError(name)
