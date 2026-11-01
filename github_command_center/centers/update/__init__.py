__all__=["UpdateCenter"]
def __getattr__(name):
    if name=="UpdateCenter":
        from .update_center import UpdateCenter
        return UpdateCenter
    raise AttributeError(name)
