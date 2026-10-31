import unittest
from github_command_center.services.diff_service import DiffParser,DiffService,word_diff
PATCH='''diff --git a/demo.py b/demo.py
index 1111111..2222222 100644
--- a/demo.py
+++ b/demo.py
@@ -1,3 +1,3 @@
 title = "Demo"
-old_value = 10
+new_value = 20
 print(title)
'''
class DiffServiceTests(unittest.TestCase):
 def test_parse_file_and_hunk(self):
  files=DiffParser.parse(PATCH);self.assertEqual(len(files),1);self.assertEqual(len(files[0].hunks),1);self.assertEqual(files[0].additions,1);self.assertEqual(files[0].deletions,1)
 def test_line_numbers(self):
  lines=DiffParser.parse(PATCH)[0].hunks[0].lines;deleted=next(x for x in lines if x.kind=="delete");added=next(x for x in lines if x.kind=="add");self.assertEqual(deleted.old_number,2);self.assertEqual(added.new_number,2)
 def test_word_diff(self):
  left,right=word_diff("old value 10","new value 20");self.assertTrue(any(k=="delete" for k,_ in left));self.assertTrue(any(k=="add" for k,_ in right))
 def test_hunk_patch(self):
  f=DiffParser.parse(PATCH)[0];value=DiffService.hunk_patch(f,f.hunks[0]);self.assertIn("diff --git a/demo.py b/demo.py",value);self.assertIn("@@ -1,3 +1,3 @@",value)
 def test_binary(self):
  f=DiffParser.parse("diff --git a/a.png b/a.png\nBinary files a/a.png and b/a.png differ\n")[0];self.assertTrue(f.binary)
