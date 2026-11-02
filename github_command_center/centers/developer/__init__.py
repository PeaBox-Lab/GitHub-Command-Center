__all__=['DeveloperToolboxCenter','GitObjectQueryCenter']
def __getattr__(name):
    if name in __all__:
        from .tools import DeveloperToolboxCenter,GitObjectQueryCenter
        return {'DeveloperToolboxCenter':DeveloperToolboxCenter,'GitObjectQueryCenter':GitObjectQueryCenter}[name]
    raise AttributeError(name)
