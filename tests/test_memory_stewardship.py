import json
import tempfile
import unittest
from pathlib import Path

from runtime.memory_stewardship import (
    deletion_guard,
    load_registry,
    registry_readback,
    release_current_relation,
    retain,
)


class MemoryStewardshipTests(unittest.TestCase):
    def test_retain_creates_verified_recovery_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            registry = root / "registry.json"
            recovery = root / "recovery"
            source.write_text("R-000\n", encoding="utf-8")

            item = retain(source, registry, recovery, item_id="R-000")
            self.assertTrue(item["preservation"]["verified"])
            self.assertTrue(Path(item["preservation"]["recovery_path"]).is_file())

            rb = registry_readback(registry)
            self.assertTrue(rb["all_pinned_items_verified"])

    def test_release_does_not_delete_source_or_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            registry = root / "registry.json"
            recovery = root / "recovery"
            source.write_text("history", encoding="utf-8")

            retain(source, registry, recovery, item_id="X")
            released = release_current_relation("X", registry, reason="noise")
            self.assertFalse(released["current_participation"])
            self.assertTrue(released["release"]["source_history_preserved"])
            self.assertTrue(source.exists())

    def test_delete_guard_blocks_without_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            registry = root / "registry.json"
            source.write_text("important", encoding="utf-8")

            result = deletion_guard(source, registry)
            self.assertFalse(result["allowed"])
            self.assertEqual(result["reason"], "NO_VERIFIED_RECOVERY_COPY")

    def test_delete_guard_allows_only_after_verified_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            registry = root / "registry.json"
            recovery = root / "recovery"
            source.write_text("important", encoding="utf-8")

            retain(source, registry, recovery, item_id="X")
            result = deletion_guard(source, registry)
            self.assertTrue(result["allowed"])
            self.assertEqual(result["reason"], "VERIFIED_RECOVERY_COPY_EXISTS")

    def test_registry_keeps_action_consequence_receipt_readback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "source.md"
            registry = root / "registry.json"
            recovery = root / "recovery"
            source.write_text("important", encoding="utf-8")

            retain(source, registry, recovery, item_id="X")
            data = load_registry(registry)
            event = data["events"][-1]
            self.assertEqual(event["action"], "CAM_GIU")
            self.assertIsNotNone(event["consequence"])
            self.assertIsNotNone(event["receipt"])
            self.assertTrue(event["readback"]["verified"])


if __name__ == "__main__":
    unittest.main()
