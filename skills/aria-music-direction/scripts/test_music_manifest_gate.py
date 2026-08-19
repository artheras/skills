from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from music_manifest_gate import has_errors, validate_manifest


VALID_MANIFEST = {
    "project_id": "harbor-recap",
    "status": "ready_for_review",
    "usage": {"mode": "licensed", "cue_id": "quiet-open"},
    "track": {
        "asset_id": "licensed-harbor-001",
        "title": "Harbor Open",
        "source": "approved music library",
        "rights": "commercial social licence",
        "license_proof": "internal://licenses/harbor-open",
        "territory": "global",
        "term": "2026-01-01 to 2026-12-31",
        "asset_status": "cleared"
    },
    "mix": {"target_lufs": -16, "ducking_db": 8, "true_peak_dbtp": -1},
    "human_approval": True,
    "financial_context": {"contains_financial_content": False}
}


class MusicManifestGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog_ids = {"quiet-open"}

    def test_valid_manifest_has_no_errors(self) -> None:
        self.assertFalse(has_errors(validate_manifest(VALID_MANIFEST, self.catalog_ids)))

    def test_released_music_requires_clearance_and_approval(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["status"] = "released"
        manifest["track"]["asset_status"] = "brief_only"
        manifest["human_approval"] = False
        codes = {finding["code"] for finding in validate_manifest(manifest, self.catalog_ids)}
        self.assertTrue({"track_not_cleared", "music_release_not_approved"}.issubset(codes))

    def test_no_music_requires_editorial_reason(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["usage"] = {"mode": "no_music"}
        del manifest["track"]
        codes = {finding["code"] for finding in validate_manifest(manifest, self.catalog_ids)}
        self.assertIn("no_music_reason_missing", codes)

    def test_invalid_mix_is_rejected(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["mix"] = {"target_lufs": -6, "ducking_db": 20, "true_peak_dbtp": 0}
        codes = {finding["code"] for finding in validate_manifest(manifest, self.catalog_ids)}
        self.assertTrue({"mix_target_invalid", "mix_ducking_invalid", "mix_true_peak_invalid"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()
