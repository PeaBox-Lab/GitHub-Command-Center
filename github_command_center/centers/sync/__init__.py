__all__=["AsyncFetchCenter","AsyncMaintenanceCenter","AsyncRemotePruneCenter","AsyncPushPullCenter"]
def __getattr__(name):
    mapping={
        "AsyncFetchCenter":(".fetch_center","AsyncFetchCenter"),
        "AsyncMaintenanceCenter":(".maintenance_center","AsyncMaintenanceCenter"),
        "AsyncRemotePruneCenter":(".remote_prune_center","AsyncRemotePruneCenter"),
        "AsyncPushPullCenter":(".push_pull_center","AsyncPushPullCenter"),
    }
    if name in mapping:
        import importlib
        mod,attr=mapping[name]
        return getattr(importlib.import_module(mod,__name__),attr)
    raise AttributeError(name)
