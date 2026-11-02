__all__=['DeveloperToolboxCenter','GitObjectQueryCenter','DevQualityCenter','CodeSearchCenter','PatchSeriesCenter','RepositoryMetricsCenter','BuildCommandCenter','DevArtifactCenter','RefCompareCenter','RevisionExplainCenter']
def __getattr__(name):
    if name in ('DeveloperToolboxCenter','GitObjectQueryCenter'):
        from .tools import DeveloperToolboxCenter,GitObjectQueryCenter
        return {'DeveloperToolboxCenter':DeveloperToolboxCenter,'GitObjectQueryCenter':GitObjectQueryCenter}[name]
    if name in ('DevQualityCenter','CodeSearchCenter','PatchSeriesCenter','RepositoryMetricsCenter','BuildCommandCenter','DevArtifactCenter','RefCompareCenter','RevisionExplainCenter'):
        from .engineering import DevQualityCenter,CodeSearchCenter,PatchSeriesCenter,RepositoryMetricsCenter,BuildCommandCenter,DevArtifactCenter,RefCompareCenter,RevisionExplainCenter
        return locals()[name]
    raise AttributeError(name)
