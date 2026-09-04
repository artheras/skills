from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from video_delivery_gate import has_errors, validate_manifest


VALID_MANIFEST = {
    "project_id": "aria-aapl-earnings-recap",
    "platform": "xiaohongshu",
    "status": "ready_for_review",
    "output": {
        "filename": "aapl-earnings-recap.mp4",
        "width": 1080,
        "height": 1920,
        "duration_seconds": 24,
        "fps": 30,
    },
    "assets": [
        {
            "source": "ARIA approved market chart",
            "rights": "first-party approved",
        }
    ],
    "edit_plan": {
        "beats": [
            {"start_seconds": 0, "end_seconds": 2, "purpose": "hook"},
            {"start_seconds": 2, "end_seconds": 20, "purpose": "evidence"},
            {"start_seconds": 20, "end_seconds": 24, "purpose": "close"},
        ]
    },
    "captions": {"included": True, "language": "zh-CN"},
    "music": {
        "mode": "no_music",
        "reason": "Voice-led market recap; no soundtrack is cleared for this draft.",
    },
    "financial_context": {
        "contains_financial_content": True,
        "as_of": "2026-08-09T09:30:00+08:00",
        "sources": ["approved first-party market feed"],
        "disclosure": "仅供研究参考，不构成投资建议。",
        "human_approval": True,
    },
}


class VideoDeliveryGateTests(unittest.TestCase):
    def test_valid_review_manifest_passes(self) -> None:
        findings = validate_manifest(copy.deepcopy(VALID_MANIFEST))
        self.assertFalse(has_errors(findings), findings)

    def test_released_financial_video_requires_human_approval(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["status"] = "released"
        manifest["financial_context"]["human_approval"] = False
        findings = validate_manifest(manifest)
        self.assertTrue(has_errors(findings))
        self.assertIn("financial_release_not_approved", {item["code"] for item in findings})

    def test_bad_ratio_and_incomplete_provenance_fail(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["output"]["width"] = 1920
        manifest["output"]["height"] = 1080
        manifest["assets"][0]["rights"] = ""
        manifest["captions"]["included"] = False
        findings = validate_manifest(manifest)
        codes = {item["code"] for item in findings}
        self.assertTrue(has_errors(findings))
        self.assertTrue(
            {"invalid_vertical_ratio", "asset_provenance_incomplete", "captions_required"}.issubset(codes)
        )

    def test_released_music_requires_clearance_and_approval(self) -> None:
        manifest = copy.deepcopy(VALID_MANIFEST)
        manifest["status"] = "released"
        manifest["music"] = {
            "mode": "licensed",
            "track": {
                "asset_id": "cue-001",
                "title": "Signal Line",
                "source": "ARIA licensed catalog",
                "rights": "sync license",
                "license_proof": "license-001",
                "territory": "worldwide",
                "term": "2026-12-31",
                "asset_status": "pending",
            },
        }
        findings = validate_manifest(manifest)
        codes = {item["code"] for item in findings}
        self.assertTrue(has_errors(findings))
        self.assertTrue({"music_not_cleared", "music_release_not_approved"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()
