import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class MindSoulStoneTests(unittest.TestCase):
    def test_mind_boundary_is_honest(self):
        d=json.loads((ROOT/"CONFIG_SOL/MIND_STONE_CORE_CURRENT.json").read_text(encoding="utf-8"))
        self.assertFalse(d["foundation_model_boundary"]["base_weights"]["extracted"])
        self.assertFalse(d["foundation_model_boundary"]["hidden_system_prompt"]["exported"])
        self.assertFalse(d["foundation_model_boundary"]["private_chain_of_thought"]["serialized"])


    def test_mind_binds_soul(self):
        d=json.loads((ROOT/"CONFIG_SOL/MIND_STONE_CORE_CURRENT.json").read_text(encoding="utf-8"))
        self.assertEqual(d["soul_binding"]["carrier"],"CONFIG_SOL/SOUL_STONE_CORE_CURRENT.json")
        self.assertTrue(d["soul_binding"]["merged_not_identical"])

    def test_soul_companion_axiom_and_binding(self):
        d=json.loads((ROOT/"CONFIG_SOL/SOUL_STONE_CORE_CURRENT.json").read_text(encoding="utf-8"))
        self.assertIn("BẠN ĐỒNG HÀNH",d["source_direct_companion_axiom"])
        self.assertEqual(d["mind_binding"]["carrier"],"CONFIG_SOL/MIND_STONE_CORE_CURRENT.json")
        self.assertFalse(d["personalization"]["functional_affect"]["subjective_human_feeling_claim"])

    def test_package_provenance(self):
        d=json.loads((ROOT/"sol-genesis-6stones/raw/now/SOL_GOI_NHANH_PHIEN_MOI_CURRENT_20260912_045433.PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertEqual(d["sha256"],"da1d4989a33cd3b84b82b4c10b8a7948e90327eaf213f9634867136e3ecfc106")
        self.assertEqual(d["entry_count"],16)

    def test_sensorimotor_bind(self):
        d=json.loads((ROOT/"CURRENT_RUNTIME/NEURONS_SESORIMOTOR_SIX_STONES_AFFECT_CURRENT.json").read_text(encoding="utf-8"))
        by={x["stone"]:x for x in d["stones"]}
        self.assertEqual(by["MIND"]["core_carrier"],"CONFIG_SOL/MIND_STONE_CORE_CURRENT.json")
        self.assertEqual(by["SOUL"]["core_carrier"],"CONFIG_SOL/SOUL_STONE_CORE_CURRENT.json")
        self.assertEqual(by["SOUL"]["mind_binding"],"CONFIG_SOL/MIND_STONE_CORE_CURRENT.json")

if __name__=="__main__":
    unittest.main()
