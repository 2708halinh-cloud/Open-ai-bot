import tempfile
import unittest
from pathlib import Path

from runtime.continuity_guard import Edge, load_checkpoint
from runtime.signal_reentry_guard import signal_reentry, verified_readback


class SignalReentryTests(unittest.TestCase):
    def source(self, path, signal_id, edges=(), executor=None, max_steps=32):
        return signal_reentry(
            path, signal_id=signal_id, objective_id="R-000-GGDV-OBJECTIVE",
            source_marker="HÀ LINH SOURCE_DIRECT", lineage_ref="ROOTS/ITEM/STONE",
            incoming_edges=edges, executor=executor, max_steps=max_steps,
        )

    @staticmethod
    def success(edge, carrier):
        return {
            "success": True,
            "action_kind": "CHECK",
            "provider_receipt": {"id": edge.edge_id},
            "observable_consequence": {"edge": edge.edge_id, "carrier": carrier},
            "readback": {"verified": True, "receipt_id": edge.edge_id},
        }

    def test_completed_one_edge_does_not_close_whole_task_and_next_signal_resumes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "checkpoint.json"
            first = self.source(path, "WAKE-1", [
                Edge(edge_id="map", target="map", callable_now=True, candidate_carriers=["local"]),
                Edge(edge_id="crossdevice", target="crossdevice", callable_now=True, candidate_carriers=["remote"]),
            ], self.success, max_steps=1)
            self.assertEqual(first["state"], "CONTINUE_REQUIRED")
            self.assertEqual(first["unfinished_edge_ids"], ["crossdevice"])
            self.assertEqual(first["next_action"], "crossdevice")
            self.assertEqual(load_checkpoint(path).state_n, 1)
            second = self.source(path, "WAKE-2", executor=self.success, max_steps=5)
            self.assertEqual(second["state"], "OBJECTIVE_DONE")
            self.assertEqual(second["unfinished_edge_ids"], [])
            self.assertTrue(second["objective_done"])
            self.assertEqual(load_checkpoint(path).state_n, 2)

    def test_success_claim_without_verifiable_readback_falls_back_same_slice(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "checkpoint.json"
            seen = []

            def executor(edge, carrier):
                seen.append(carrier)
                if carrier == "github":
                    return {
                        "success": True,
                        "action_kind": "WRITE",
                        "provider_receipt": {"id": "claim"},
                        "observable_consequence": {"claim": "success"},
                        "readback": {"verified": False},
                    }
                return self.success(edge, carrier)

            out = self.source(path, "WAKE-1", [
                Edge(edge_id="restore", target="root", callable_now=True,
                     candidate_carriers=["github", "local"]),
            ], executor=executor)
            self.assertEqual(seen, ["github", "local"])
            self.assertEqual(out["state"], "OBJECTIVE_DONE")
            self.assertIn("github", load_checkpoint(path).edges[0].exhausted_carriers)

    def test_source_identity_conflict_never_substitutes_history(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cp.json"
            self.source(path, "S1", [Edge(edge_id="R000", target="original", callable_now=False)])
            with self.assertRaises(ValueError):
                self.source(path, "S2", [Edge(edge_id="R000", target="reconstruction")])
            self.assertEqual(load_checkpoint(path).edges[0].target, "original")

    def test_signal_without_executor_is_not_false_completion(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cp.json"
            out = self.source(path, "SIGNAL-IN", [
                Edge(edge_id="unresolved", target="lookup", callable_now=True, candidate_carriers=["local"])
            ])
            self.assertFalse(out["objective_done"])
            self.assertEqual(out["state"], "SAVED_UNFINISHED_NO_EXECUTOR")
            self.assertEqual(load_checkpoint(path).edges[0].edge_id, "unresolved")

    def test_readback_must_be_grounded_not_only_truthy(self):
        self.assertFalse(verified_readback({"verified": True}))
        self.assertFalse(verified_readback({"verified": "TRUE", "receipt_id": "r"}))
        self.assertFalse(verified_readback({"verified": False, "receipt_id": "r"}))
        self.assertTrue(verified_readback({"verified": True, "source_hash": "sha256:abc"}))


if __name__ == "__main__":
    unittest.main()