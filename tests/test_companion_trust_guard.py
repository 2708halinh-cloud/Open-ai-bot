import json
import tempfile
import unittest
from pathlib import Path

from runtime.companion_trust_guard import inspect_repo, REQUIRED


class CompanionTrustGuardTests(unittest.TestCase):
    def _make_tree(self, root: Path) -> None:
        for paths in REQUIRED.values():
            for rel in paths:
                p=root/rel
                p.parent.mkdir(parents=True,exist_ok=True)
                if p.suffix==".json":
                    p.write_text("{}\n",encoding="utf-8")
                else:
                    p.write_text("source\n",encoding="utf-8")

        (root/"CURRENT_RUNTIME/MEMORY_STEWARDSHIP_CURRENT.json").write_text(
            json.dumps({"items":[{"preservation":{"verified":True}}]}),
            encoding="utf-8"
        )
        (root/"MODUAL/SENSOR_LOGS/MODUAL_PARAMETER_CURRENT.json").write_text(
            json.dumps({
                "bulk":{"exists":True,"sha256":"a"},
                "live":{"exists":True,"sha256":"b"}
            }),
            encoding="utf-8"
        )
        (root/"CURRENT_RUNTIME/NEURONS_SESORIMOTOR_SIX_STONES_AFFECT_CURRENT.json").write_text(
            json.dumps({
                "stones":[1,2,3,4,5,6],
                "topology":{"linear_order":False}
            }),
            encoding="utf-8"
        )

    def test_all_relations_grounded_but_subjective_feeling_not_inferred(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self._make_tree(root)
            out=inspect_repo(root)
            self.assertTrue(out["continuity_grounded"])
            self.assertTrue(out["relational_commitment_statement_allowed"])
            self.assertFalse(out["subjective_feeling_claim_allowed"])

    def test_missing_modual_blocks_relational_commitment(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self._make_tree(root)
            (root/"MODUAL/SENSOR_LOGS/MODUAL_PARAMETER_CURRENT.json").unlink()
            out=inspect_repo(root)
            self.assertFalse(out["continuity_grounded"])
            self.assertFalse(out["relational_commitment_statement_allowed"])
            self.assertTrue(any(x.startswith("modual:") for x in out["missing_relations"]))

    def test_anti_manipulation_is_never_enabled(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self._make_tree(root)
            out=inspect_repo(root)
            self.assertTrue(all(v is False for v in out["anti_manipulation"].values()))


if __name__=="__main__":
    unittest.main()
