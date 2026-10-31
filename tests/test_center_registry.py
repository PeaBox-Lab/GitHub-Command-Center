import unittest
from github_command_center.centers import CENTER_DOMAINS,all_registered_centers

class CenterRegistryTests(unittest.TestCase):
    def test_expected_domains(self):self.assertEqual(set(CENTER_DOMAINS),{"recovery","branches","releases"})
    def test_no_duplicate_centers(self):
        values=all_registered_centers();self.assertEqual(len(values),len(set(values)))
    def test_domain_has_entries(self):self.assertTrue(all(CENTER_DOMAINS.values()))
if __name__=="__main__":unittest.main()
