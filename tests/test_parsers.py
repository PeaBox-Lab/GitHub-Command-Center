import unittest
from github_command_center.services.parsers import parse_for_each_ref, parse_nul_paths, parse_status_porcelain_v1

class ParserTests(unittest.TestCase):
    def test_status_normal(self):
        rows=parse_status_porcelain_v1(" M README.md\nA  new.py\n")
        self.assertEqual([(r.x,r.y,r.path) for r in rows],[(" ","M","README.md"),("A"," ","new.py")])
    def test_status_rename(self):
        row=parse_status_porcelain_v1("R  old.txt -> new.txt\n")[0]
        self.assertEqual(row.original_path,"old.txt");self.assertEqual(row.path,"new.txt")
    def test_nul_paths(self):self.assertEqual(parse_nul_paths(b"a b.txt\0c.txt\0"),["a b.txt","c.txt"])
    def test_refs(self):self.assertEqual(parse_for_each_ref("main\torigin/main\tabc\n"),[("main","origin/main","abc")])
if __name__=="__main__":unittest.main()
