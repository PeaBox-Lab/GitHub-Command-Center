import unittest
from pathlib import Path
from github_command_center.models import CommandResult,RepositoryState
class ModelTests(unittest.TestCase):
    def test_result(self):
        r=CommandResult(("git","status"),Path("."),0);self.assertTrue(r.ok);self.assertEqual(r.output,"Completed successfully.")
    def test_state(self):
        s=RepositoryState(Path("."),branch="",changed_paths=[" M x"]);self.assertTrue(s.detached);self.assertFalse(s.clean)
if __name__=="__main__":unittest.main()
