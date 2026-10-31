import ast
import unittest
from pathlib import Path

class AsyncPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parents[1]/"github_command_center"/"centers"/"async_operations.py"
        tree=ast.parse(path.read_text(encoding="utf-8"))
        cls.presets=None
        for node in tree.body:
            if isinstance(node,ast.ClassDef) and node.name=="AsyncOperationsCenter":
                for item in node.body:
                    if isinstance(item,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="PRESETS" for t in item.targets):cls.presets=ast.literal_eval(item.value)
        assert cls.presets is not None
    def test_arrays(self):
        for v in self.presets.values():self.assertEqual(v[0],"git");self.assertIsInstance(v,list)
    def test_long_ops(self):self.assertTrue({"Fetch all + prune","Full fsck","Auto maintenance","Normal gc"}.issubset(self.presets))
if __name__=="__main__":unittest.main()
