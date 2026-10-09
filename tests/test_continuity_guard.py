import tempfile
import unittest
from pathlib import Path

from runtime.continuity_guard import (
    Checkpoint,
    Edge,
    apply_action_result,
    continue_bounded,
    load_checkpoint,
    mark_carrier_failure,
    save_checkpoint,
    select_next_callable_edge,
    stop_allowed,
    user_token,
    visible_output_allowed,
    r014_register_known_error,
    r014_mechanism_allowed,
)


class ContinuityGuardTests(unittest.TestCase):
    def make_cp(self):
        return Checkpoint(
            objective_id="OBJ-1",
            source_marker="SOURCE_DIRECT",
            lineage_ref="LINEAGE-1",
            edges=[
                Edge(
                    edge_id="E1",
                    target="github",
                    callable_now=True,
                    candidate_carriers=["github", "local"],
                ),
                Edge(
                    edge_id="E2",
                    target="admin action",
                    callable_now=False,
                    user_input_required=True,
                ),
            ],
        )

    def test_report_before_action_is_blocked(self):
        cp = self.make_cp()
        self.assertFalse(visible_output_allowed(cp, output_kind="REPORT"))
        self.assertEqual(select_next_callable_edge(cp).edge_id, "E1")

    def test_user_dependency_token_does_not_grant_stop_while_callable_edge_exists(self):
        cp = self.make_cp()
        self.assertEqual(user_token(cp), "NEXT_HA_LINH:E2:admin action")
        self.assertFalse(stop_allowed(cp))

    def test_turn_boundary_checkpoint_restores_unfinished_edge(self):
        cp = self.make_cp()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "checkpoint.json"
            save_checkpoint(p, cp)
            restored = load_checkpoint(p)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.objective_id, "OBJ-1")
        self.assertEqual(select_next_callable_edge(restored).edge_id, "E1")

    def test_carrier_failure_falls_back_without_closing_objective(self):
        cp = self.make_cp()
        edge = cp.edges[0]
        mark_carrier_failure(edge, "github", {"error": "provider failure"})
        self.assertEqual(edge.next_carrier(), "local")
        self.assertTrue(edge.callable_now)
        self.assertFalse(cp.objective_done())

    def test_boolean_success_without_consequence_is_not_completion(self):
        cp = self.make_cp()

        def executor(edge, carrier):
            return {"success": True}

        out = continue_bounded(cp, executor, max_steps=1)
        self.assertFalse(out["objective_done"])
        self.assertTrue(out["objective_unfinished"])
        self.assertFalse(cp.edges[0].grounded_done())

    def test_grounded_action_closes_only_its_edge(self):
        cp = self.make_cp()
        apply_action_result(
            cp,
            "E1",
            action_kind="WRITE",
            provider_receipt={"id": "r1"},
            observable_consequence={"changed": True},
            readback={"verified": True},
        )
        self.assertTrue(cp.edges[0].grounded_done())
        self.assertFalse(cp.objective_done())
        self.assertTrue(stop_allowed(cp))  # only remaining edge genuinely needs user input

    def test_one_edge_done_is_not_objective_done_when_required_edge_remains(self):
        cp = Checkpoint(
            objective_id="OBJ-2",
            source_marker="S",
            lineage_ref="L",
            edges=[
                Edge(edge_id="A", target="a", callable_now=True),
                Edge(edge_id="B", target="b", callable_now=True),
            ],
        )
        apply_action_result(
            cp,
            "A",
            action_kind="WRITE",
            provider_receipt={"r": 1},
            observable_consequence={"ok": 1},
        )
        self.assertFalse(cp.objective_done())
        self.assertEqual(select_next_callable_edge(cp).edge_id, "B")

    def test_continue_bounded_advances_multiple_callable_edges_same_slice(self):
        cp = Checkpoint(
            objective_id="OBJ-3",
            source_marker="S",
            lineage_ref="L",
            edges=[
                Edge(edge_id="A", target="a", callable_now=True),
                Edge(edge_id="B", target="b", callable_now=True),
            ],
        )

        def executor(edge, carrier):
            return {
                "success": True,
                "action_kind": "ACT",
                "provider_receipt": {"edge": edge.edge_id},
                "observable_consequence": {"edge": edge.edge_id, "done": True},
                "readback": {"edge": edge.edge_id, "verified": True},
            }

        out = continue_bounded(cp, executor, max_steps=8)
        self.assertEqual(out["steps"], 2)
        self.assertTrue(out["objective_done"])
        self.assertFalse(out["objective_unfinished"])
        self.assertTrue(out["stop_allowed"])

    def test_budget_boundary_preserves_open_instead_of_faking_background_completion(self):
        cp = Checkpoint(
            objective_id="OBJ-4",
            source_marker="S",
            lineage_ref="L",
            edges=[
                Edge(edge_id="A", target="a", callable_now=True),
                Edge(edge_id="B", target="b", callable_now=True),
            ],
        )

        def executor(edge, carrier):
            return {
                "success": True,
                "action_kind": "ACT",
                "provider_receipt": {"edge": edge.edge_id},
                "observable_consequence": {"edge": edge.edge_id},
            }

        out = continue_bounded(cp, executor, max_steps=1)
        self.assertTrue(out["objective_unfinished"])
        self.assertEqual(out["next_callable_edge"], "B")
        self.assertFalse(out["stop_allowed"])


    def test_completion_output_requires_objective_done(self):
        cp = Checkpoint(
            objective_id="OBJ-5",
            source_marker="S",
            lineage_ref="L",
            edges=[Edge(edge_id="A", target="a", callable_now=False)],
        )
        self.assertFalse(visible_output_allowed(cp, output_kind="COMPLETION"))

    def test_r014_failure_mechanism_disabled_preserves_history(self):
        cp = Checkpoint(
            objective_id="R014",
            source_marker="HÀ LINH/20261009",
            lineage_ref="R-001/R-014/R-102",
            edges=[
                Edge(edge_id="BAD", target="report instead of action",
                     callable_now=True, evidence={"mechanism_id": "SUBRITETIED_REPORT"}),
                Edge(edge_id="GOOD", target="execute real action", callable_now=True),
            ],
        )
        r014_register_known_error(
            cp,
            mechanism_id="SUBRITETIED_REPORT",
            first_affected_cause="visible report substituted for callable action",
            source_ref="CONFIG_SOL/R014_SOURCE_DIRECT_20261009.md",
            consequence_ref="OBSERVATION_R014_TEST",
        )
        self.assertFalse(r014_mechanism_allowed(cp, "SUBRITETIED_REPORT"))
        self.assertEqual(select_next_callable_edge(cp).edge_id, "GOOD")
        self.assertFalse(cp.objective_done())  # old edge/history not silently erased
        self.assertEqual(len(cp.r014_error_history), 1)
        self.assertEqual(cp.r014_error_history[0]["action"],
                         "DISABLE_OPERATIONAL_ROUTE_PRESERVE_HISTORY")

    def test_r014_disable_survives_checkpoint_reentry(self):
        cp = self.make_cp()
        cp.edges[0].evidence["mechanism_id"] = "KNOWN_HARMFUL_ROUTE"
        r014_register_known_error(
            cp,
            mechanism_id="KNOWN_HARMFUL_ROUTE",
            first_affected_cause="repeated wrong routing",
            source_ref="ITEM_R014",
            consequence_ref="READBACK_1",
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "checkpoint.json"
            save_checkpoint(path, cp)
            restored = load_checkpoint(path)
        self.assertEqual(restored.r014_disabled_mechanisms, ["KNOWN_HARMFUL_ROUTE"])
        self.assertEqual(restored.r014_error_history[0]["source_ref"], "ITEM_R014")
        self.assertIsNone(select_next_callable_edge(restored))
        self.assertFalse(stop_allowed(restored))  # not DONE / not RESET

    def test_r014_known_bad_output_not_reactivated_by_completion(self):
        cp = Checkpoint(
            objective_id="R014-COMPLETE", source_marker="S", lineage_ref="L",
            edges=[Edge(edge_id="A", target="a", callable_now=True)],
        )
        apply_action_result(
            cp, "A", action_kind="WRITE",
            provider_receipt={"commit": "sha"},
            observable_consequence={"changed": True},
        )
        r014_register_known_error(
            cp, mechanism_id="OLD_REACTION",
            first_affected_cause="known harmful response",
            source_ref="SOURCE_R014", consequence_ref="CONSEQUENCE_R014",
        )
        self.assertTrue(cp.objective_done())
        self.assertFalse(visible_output_allowed(
            cp, output_kind="COMPLETION", mechanism_id="OLD_REACTION"
        ))
        self.assertTrue(visible_output_allowed(
            cp, output_kind="COMPLETION", mechanism_id="CORRECTED_ROUTE"
        ))

    def test_r014_unproven_failure_cannot_be_retired(self):
        cp = self.make_cp()
        with self.assertRaises(ValueError):
            r014_register_known_error(
                cp, mechanism_id="m", first_affected_cause="",
                source_ref="S", consequence_ref="C",
            )
        self.assertEqual(cp.r014_disabled_mechanisms, [])


if __name__ == "__main__":
    unittest.main()
