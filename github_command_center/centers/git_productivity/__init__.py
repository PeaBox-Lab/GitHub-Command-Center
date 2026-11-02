__all__=['GitLogVisualizerCenter','StashWorkbenchCenter','WorktreeWorkbenchCenter','CommitGraphFilterCenter','StashConflictPreviewCenter']
def __getattr__(name):
    if name in __all__:
        from .productivity import GitLogVisualizerCenter,StashWorkbenchCenter,WorktreeWorkbenchCenter,CommitGraphFilterCenter,StashConflictPreviewCenter
        return locals()[name]
    raise AttributeError(name)
