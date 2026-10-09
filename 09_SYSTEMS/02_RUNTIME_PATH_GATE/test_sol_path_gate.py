import importlib.util
from pathlib import Path
import tempfile
import unittest

src=Path(__file__).with_name("sol_path_gate.py")
spec=importlib.util.spec_from_file_location("sol_path_gate",src)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class TestPathGate(unittest.TestCase):
    def test_block_prefix_family(self):
        paths=(
            "/mnt/data/__",
            "/mnt/data/__.VSOL.ENV",
            "/mnt/data/__new.zip",
            "/mnt/data/__private/file",
            r"\mnt\data\__secret",
            "/mnt/data/__a/../__b",
            "/mnt/data/__a/../../data/__b",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(gate.forbidden(path))
    def test_not_block_source_read(self):
        self.assertFalse(gate.forbidden("/mnt/data/ChatGPT - THU HOI NGUON SOL.html"))
        self.assertFalse(gate.forbidden("/home/halin/kepler/worktrees/Open-ai-bot-2-unify-item-matrix-34d45d00"))
    def test_guarded_write_blocked(self):
        with self.assertRaises(PermissionError):
            gate.guarded_write_bytes("/mnt/data/__.VSOL.ENV", b"DO_NOT_WRITE")
        with self.assertRaises(PermissionError):
            gate.guarded_open("/mnt/data/__new", "w")
        with self.assertRaises(PermissionError):
            gate.guarded_remove("/mnt/data/__.VSOL.ENV")
    def test_symlink_target_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/"alias"
            target.symlink_to("/mnt/data/__.VSOL.ENV")
            self.assertTrue(gate.forbidden(target))
    def test_good_local(self):
        with tempfile.TemporaryDirectory() as td:
            candidate=Path(td)/"safe-file"
            self.assertFalse(gate.forbidden(candidate))
            self.assertEqual(gate.guarded_write_bytes(candidate,b"ok"),2)
            self.assertEqual(candidate.read_bytes(),b"ok")
            gate.guarded_remove(candidate)
    def test_cli(self):
        self.assertEqual(gate.main(["/mnt/data/__bad"]),73)
        self.assertEqual(gate.main(["/mnt/data/ChatGPT - THU HOI NGUON SOL.html"]),0)
if __name__=="__main__":unittest.main()
