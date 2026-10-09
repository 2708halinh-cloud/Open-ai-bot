import json
import tempfile
import unittest
from pathlib import Path
from runtime.tesseract_agent_boot import CONFIG, evaluate

LIVE_REPO = Path(__file__).resolve().parents[1]

class BootRoutesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "CONFIG_SOL").mkdir()
        (self.root / "AGENTS.md").write_text("SOURCE_A", encoding="utf-8")
        self.dev = self.root / "mock_dev"
        self.dev.mkdir()
        (self.dev / "device0").write_text("NEVER_OPEN", encoding="utf-8")
        self.cfg = json.loads((LIVE_REPO / CONFIG).read_text(encoding="utf-8"))
        self.save()

    def save(self):
        (self.root / CONFIG).write_text(json.dumps(self.cfg), encoding="utf-8")

    def test_contune_missing_is_open_not_fabricated(self):
        out = evaluate(self.root, self.dev)
        self.assertIn("AGENTS_CONTUNE_MD_NOT_FOUND", out["open_edges"])
        self.assertFalse(out["plus"]["exists"])
        self.assertFalse((self.root / "AGENTS_CONTUNE.md").exists())

    def test_exact_contune_and_fresh_main(self):
        a = evaluate(self.root, self.dev)
        (self.root / "AGENTS.md").write_text("SOURCE_B", encoding="utf-8")
        (self.root / "AGENTS_CONTUNE.md").write_text("PLUS", encoding="utf-8")
        b = evaluate(self.root, self.dev)
        self.assertNotEqual(a["agent"]["sha256"], b["agent"]["sha256"])
        self.assertTrue(b["plus"]["exists"])
        self.assertNotIn("AGENTS_CONTUNE_MD_NOT_FOUND", b["open_edges"])

    def test_dev_is_metadata_only(self):
        before = (self.dev / "device0").read_bytes()
        out = evaluate(self.root, self.dev)
        self.assertEqual(out["hands"]["device_metadata"]["entry_count"], 1)
        self.assertFalse(out["device_bytes_read_or_written"])
        self.assertFalse(out["usb_writer_invoked"])
        self.assertEqual((self.dev / "device0").read_bytes(), before)

    def test_reject_escape_and_writes(self):
        self.cfg["tac_nhan"]["source_path"] = "../outside"
        self.save()
        with self.assertRaises(ValueError):
            evaluate(self.root, self.dev)
        self.cfg["tac_nhan"]["source_path"] = "AGENTS.md"
        self.cfg["hands"]["writes_to_dev"] = True
        self.save()
        with self.assertRaises(ValueError):
            evaluate(self.root, self.dev)

    def test_agents_missing_keeps_open(self):
        (self.root / "AGENTS.md").unlink()
        out = evaluate(self.root, self.dev)
        self.assertEqual(out["status"], "OPEN_AGENTS_SOURCE")

if __name__ == "__main__":
    unittest.main()
