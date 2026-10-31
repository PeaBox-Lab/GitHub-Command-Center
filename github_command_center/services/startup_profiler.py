from __future__ import annotations
import importlib,time
from dataclasses import asdict,dataclass

@dataclass(slots=True)
class StartupProbe:
    name:str
    seconds:float
    ok:bool
    detail:str=""

class StartupProfiler:
    DEFAULT_MODULES=(
        "github_command_center.models",
        "github_command_center.services.git_service",
        "github_command_center.services.diff_service",
        "github_command_center.services.job_service",
        "github_command_center.ui.navigation",
    )
    def time_import(self,name:str)->StartupProbe:
        start=time.perf_counter()
        try:
            importlib.invalidate_caches();importlib.import_module(name)
            return StartupProbe(name,time.perf_counter()-start,True)
        except Exception as exc:return StartupProbe(name,time.perf_counter()-start,False,str(exc))
    def run(self,modules=None):return [self.time_import(x) for x in (modules or self.DEFAULT_MODULES)]
    @staticmethod
    def total(values):return sum(x.seconds for x in values)
    @staticmethod
    def serializable(values):return [asdict(x) for x in values]
