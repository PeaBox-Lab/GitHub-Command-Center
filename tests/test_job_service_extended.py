import sys,tempfile,time,unittest
from pathlib import Path
from github_command_center.services import JobService
class JobServiceExtendedTests(unittest.TestCase):
 def wait(self,j):
  end=time.time()+5
  while j.status in ("Queued","Running") and time.time()<end:time.sleep(.02)
 def test_failure(self):
  with tempfile.TemporaryDirectory() as d:
   s=JobService();j=s.submit([sys.executable,"-c","raise SystemExit(7)"],Path(d));self.wait(j);self.assertEqual(j.status,"Failed");self.assertEqual(j.returncode,7);self.assertIsNone(j.process)
 def test_cancel(self):
  with tempfile.TemporaryDirectory() as d:
   s=JobService();j=s.submit([sys.executable,"-c","import time;time.sleep(10)"],Path(d));time.sleep(.15);self.assertTrue(s.cancel(j.job_id));self.wait(j);self.assertEqual(j.status,"Cancelled")
 def test_events(self):
  with tempfile.TemporaryDirectory() as d:
   s=JobService();j=s.submit([sys.executable,"-c","print('event')"],Path(d));self.wait(j);seen=[];s.drain_events(lambda *x:seen.append(x));self.assertTrue(any(x[1]=="output" for x in seen))
