import sys,tempfile,time,unittest
from pathlib import Path
from github_command_center.services import JobService

class JobServiceTests(unittest.TestCase):
    def test_job_completes_and_streams(self):
        with tempfile.TemporaryDirectory() as folder:
            service=JobService();job=service.submit([sys.executable,"-c","print('hello')"],Path(folder))
            deadline=time.time()+10
            while job.status in ("Queued","Running") and time.time()<deadline:time.sleep(.02)
            self.assertEqual(job.status,"Completed");self.assertEqual(job.returncode,0);self.assertIn("hello",''.join(job.output))
    def test_cancel_missing_job(self):self.assertFalse(JobService().cancel(999))
if __name__=="__main__":unittest.main()
