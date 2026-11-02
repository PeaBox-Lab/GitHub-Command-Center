__all__=['DeveloperToolboxCenter','GitObjectQueryCenter','DevQualityCenter','CodeSearchCenter','PatchSeriesCenter','RepositoryMetricsCenter','BuildCommandCenter','DevArtifactCenter']
def __getattr__(name):
    if name in ('DeveloperToolboxCenter','GitObjectQueryCenter'):
        from .tools import DeveloperToolboxCenter,GitObjectQueryCenter
        return {'DeveloperToolboxCenter':DeveloperToolboxCenter,'GitObjectQueryCenter':GitObjectQueryCenter}[name]
    if name in ('DevQualityCenter','CodeSearchCenter','PatchSeriesCenter','RepositoryMetricsCenter','BuildCommandCenter','DevArtifactCenter'):
        from .engineering import DevQualityCenter,CodeSearchCenter,PatchSeriesCenter,RepositoryMetricsCenter,BuildCommandCenter,DevArtifactCenter
        return locals()[name]
    raise AttributeError(name)
