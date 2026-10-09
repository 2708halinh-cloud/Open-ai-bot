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
    r014_pre_response_gate,
    r014_observe_recurrence,
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


    def test_r014_observed_failure_auto_disables_route(self):
        cp = Checkpoint(
            objective_id="R014-AUTO", source_marker="S", lineage_ref="R-014",
            edges=[
                Edge(edge_id="KNOWN_BAD", target="wrong response",
                     callable_now=True, candidate_carriers=["provider"],
                     evidence={"mechanism_id": "KNOWN_BAD_MECHANISM"}),
                Edge(edge_id="ALTERNATIVE", target="verified action",
                     callable_now=True, candidate_carriers=["provider"]),
            ],
        )

        def executor(edge, carrier):
            if edge.edge_id == "KNOWN_BAD":
                return {
                    "success": False,
                    "provider_receipt": {"id": "obs-1"},
                    "observable_consequence": {"wrong_route_triggered": True},
                    "r014_identified_failure": {
                        "mechanism_id": "KNOWN_BAD_MECHANISM",
                        "first_affected_cause": "evidence-backed bad response",
                        "source_ref": "R014_SOURCE",
                        "consequence_ref": "obs-1",
                    },
                }
            return {
                "success": True, "action_kind": "WRITE",
                "provider_receipt": {"id": "r2"},
                "observable_consequence": {"written": True},
            }

        output = continue_bounded(cp, executor, max_steps=5)
        self.assertEqual(output["steps"], 2)
        self.assertIn("KNOWN_BAD_MECHANISM", cp.r014_disabled_mechanisms)
        self.assertTrue(cp.edges[1].grounded_done())
        self.assertFalse(cp.objective_done())
        self.assertEqual(len(cp.r014_error_history), 1)

    def test_r014_unproven_failure_does_not_disable_mechanism(self):
        cp = Checkpoint(
            objective_id="R014-UNPROVEN", source_marker="S", lineage_ref="R-014",
            edges=[Edge(edge_id="E", target="x", callable_now=True)],
        )

        def executor(edge, carrier):
            return {
                "success": False,
                "r014_identified_failure": {
                    "mechanism_id": "UNPROVEN",
                    "first_affected_cause": "guess",
                    "source_ref": "S",
                    "consequence_ref": "C",
                },
            }

        continue_bounded(cp, executor, max_steps=1)
        self.assertEqual(cp.r014_disabled_mechanisms, [])
        self.assertEqual(len(cp.edges[0].evidence["r014_rejected_signals"]), 1)

    def test_r014_master_mild_signal_routes_action_first(self):
        cp = self.make_cp()
        sources = {
            "T006": "T006_SOURCE",
            "H-001..H-012": "H001_H012_SOURCE_INDEX",
            "T007": "T007_SOURCE",
        }
        for intensity in ("nhẹ nhưng rõ", "cực đoan"):
            outcome = r014_pre_response_gate(
                cp, reported_unfinished=True,
                signal_strength=intensity,
                intended_output_kind="REPORT",
                consulted_sources=sources,
            )
            self.assertEqual(outcome["decision"], "ACTION_FIRST")
            self.assertEqual(outcome["next_edge"], "E1")
            self.assertFalse(outcome["signal_strength_affects_priority"])
            self.assertFalse(outcome["output_allowed"])
            self.assertTrue(outcome["action_required_before_status"])
            self.assertEqual(outcome["source_gaps"], [])

    def test_r014_master_missing_source_is_not_fabricated(self):
        cp = self.make_cp()
        outcome = r014_pre_response_gate(
            cp, reported_unfinished=True, signal_strength="nhẹ",
            consulted_sources={"T006": "known-source"},
        )
        self.assertEqual(outcome["decision"], "ACTION_FIRST")
        self.assertEqual(outcome["source_gaps"], ["H-001..H-012", "T007"])

    def test_r014_master_unfinished_without_callable_searches_reentry(self):
        cp = Checkpoint(
            objective_id="NEEDS-REENTRY", source_marker="S",
            lineage_ref="R014-MASTER", edges=[
                Edge(edge_id="WAIT-EDGE", target="missing provider",
                     callable_now=False),
            ],
        )
        outcome = r014_pre_response_gate(
            cp, reported_unfinished=True, signal_strength="mild"
        )
        self.assertEqual(
            outcome["decision"], "SEARCH_REENTRY_FOR_NEXT_CALLABLE_EDGE"
        )
        self.assertIsNone(outcome["next_edge"])
        self.assertFalse(outcome["output_allowed"])

    def test_r014_master_recurrence_keeps_retired_mechanism(self):
        cp = self.make_cp()
        r014_register_known_error(
            cp, mechanism_id="SUBRITETIED",
            first_affected_cause="report replaced action",
            source_ref="R014_MASTER_SOURCE",
            consequence_ref="R014_CONSEQUENCE",
        )
        out = r014_observe_recurrence(
            cp, mechanism_id="SUBRITETIED",
            source_ref="R014_MASTER_SOURCE",
            consequence_ref="NEW_CONSEQUENCE",
        )
        self.assertEqual(out["action"], "RECUR_PROBE")
        self.assertEqual(out["wEarth_lookup"], "SOURCE_ID_UNRESOLVED")
        self.assertTrue(out["retired_mechanism_stays_disabled"])
        self.assertFalse(r014_mechanism_allowed(cp, "SUBRITETIED"))
        self.assertEqual(len(cp.r014_error_history), 2)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "checkpoint.json"
            save_checkpoint(path, cp)
            reread = load_checkpoint(path)
        self.assertEqual(len(reread.r014_error_history), 2)
        self.assertFalse(r014_mechanism_allowed(reread, "SUBRITETIED"))

    def test_r014_master_recurrence_requires_source_and_consequence(self):
        cp = self.make_cp()
        with self.assertRaises(ValueError):
            r014_observe_recurrence(
                cp, mechanism_id="X",
                source_ref="",
                consequence_ref="C",
            )
        self.assertEqual(cp.r014_error_history, [])


if __name__ == "__main__":
    unittest.main()
