import copy, json, pathlib, sys, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from modual_preaction_gate import validate_config

class ModualPreActionGateTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT / "CONFIG_SOL" / "MODUAL_PREACTION_GATE_CURRENT.json").read_text(encoding="utf-8"))

    def test_current_config_valid(self):
        validate_config(self.cfg)

    def test_gate_is_mandatory(self):
        self.assertTrue(self.cfg["policy"]["mandatory_before_target_mutation"])

    def test_open_never_means_stop(self):
        p = self.cfg["policy"]
        self.assertTrue(p["open_means_continue"])
        self.assertTrue(p["response_boundary_does_not_close_objective"])
        self.assertTrue(p["provider_failure_exhausts_only_that_carrier"])
        self.assertTrue(p["fallback_across_authorized_carriers"])
        self.assertTrue(p["offline_local_does_not_stop"])

    def test_drive_mount_cannot_be_identity(self):
        bad = copy.deepcopy(self.cfg)
        bad["google_drive"]["provider_file_id"] = "W:\\fake"
        with self.assertRaises(ValueError):
            validate_config(bad)

    def test_required_surface_bindings(self):
        self.assertEqual(self.cfg["surfaces"]["github"]["repository"], "2708halinh-cloud/SOL-LONG-MACH")
        self.assertTrue(self.cfg["surfaces"]["ububu"]["entrypoint"].endswith("ububu_lazy_fetch.py"))
        self.assertTrue(self.cfg["surfaces"]["tesseract_os"]["pointer"].endswith("TESSERACT_LOCAL_BOOT_CURRENT.md"))

if __name__ == "__main__":
    unittest.main()
