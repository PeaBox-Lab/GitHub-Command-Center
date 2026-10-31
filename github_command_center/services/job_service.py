from __future__ import annotations
import subprocess, threading
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from typing import Callable, Sequence

@dataclass(slots=True)
class BackgroundJob:
    job_id:int; args:tuple[str,...]; cwd:Path; status:str="Queued"; returncode:int|None=None
    output:list[str]=field(default_factory=list); process:subprocess.Popen|None=field(default=None,repr=False)

class JobService:
    def __init__(self):
        self._next_id=1; self.jobs={}; self.events=Queue(); self._lock=threading.Lock()
    def submit(self,args:Sequence[str],cwd:str|Path)->BackgroundJob:
        if not args: raise ValueError("A background job requires command arguments.")
        with self._lock:
            job=BackgroundJob(self._next_id,tuple(map(str,args)),Path(cwd).resolve());self._next_id+=1;self.jobs[job.job_id]=job
        threading.Thread(target=self._worker,args=(job,),daemon=True).start();return job
    def _worker(self,job):
        job.status="Running";self.events.put((job.job_id,"status",job.status));stream=None
        try:
            job.process=subprocess.Popen(job.args,cwd=job.cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding="utf-8",errors="replace")
            stream=job.process.stdout
            for line in iter(stream.readline,""):
                job.output.append(line);self.events.put((job.job_id,"output",line))
            job.process.wait();job.returncode=job.process.returncode
            if job.status!="Cancelled":job.status="Completed" if job.returncode==0 else "Failed"
        except Exception as exc:
            job.output.append(str(exc));job.returncode=-1
            if job.status!="Cancelled":job.status="Failed"
        finally:
            if stream is not None:stream.close()
            job.process=None;self.events.put((job.job_id,"status",job.status));self.events.put((job.job_id,"returncode",job.returncode))
    def cancel(self,job_id:int)->bool:
        job=self.jobs.get(job_id)
        if not job or not job.process or job.process.poll() is not None:return False
        job.status="Cancelled";job.process.terminate();self.events.put((job.job_id,"status",job.status));return True
    def drain_events(self,callback:Callable):
        while not self.events.empty():callback(*self.events.get_nowait())
