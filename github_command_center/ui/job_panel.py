import tkinter as tk
from tkinter import ttk
from ..services import JobService
class JobPanel(ttk.Frame):
    def __init__(self,master,job_service=None,poll_ms=100):
        super().__init__(master);self.service=job_service or JobService();self.poll_ms=poll_ms;self.active_job_id=None;self.status=tk.StringVar(value="Ready");self._build();self.after(poll_ms,self._poll)
    def _build(self):
        b=ttk.Frame(self);b.pack(fill="x");ttk.Label(b,textvariable=self.status).pack(side="left");self.cancel_button=ttk.Button(b,text="Cancel",command=self.cancel,state="disabled");self.cancel_button.pack(side="right");self.output=tk.Text(self,wrap="none",height=14,font=("Consolas",9),bg="#0f172a",fg="#e2e8f0");self.output.pack(fill="both",expand=True,pady=(4,0))
    def start(self,args,cwd):
        j=self.service.submit(args,cwd);self.active_job_id=j.job_id;self.status.set(f"Running job {j.job_id}");self.cancel_button.configure(state="normal");self.output.delete("1.0","end");self.output.insert("end","$ "+" ".join(map(str,args))+"\n\n");return j
    def cancel(self):
        if self.active_job_id is not None and self.service.cancel(self.active_job_id):self.status.set(f"Cancelling job {self.active_job_id}")
    def _poll(self):self.service.drain_events(self._event);self.after(self.poll_ms,self._poll)
    def _event(self,jid,event,value):
        if jid!=self.active_job_id:return
        if event=="output":self.output.insert("end",str(value));self.output.see("end")
        elif event=="status":
            self.status.set(f"Job {jid}: {value}")
            if value in ("Completed","Failed","Cancelled"):self.cancel_button.configure(state="disabled")
        elif event=="returncode":self.output.insert("end",f"\nExit code: {value}\n")
