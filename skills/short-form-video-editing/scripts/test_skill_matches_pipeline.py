"""The skill must describe the pipeline that exists.

Every expensive problem in this skill came from the two drifting apart: it
named three tools that do not exist, a Veo version that is not used, output
files the renderer does not write, and an edit-plan schema with no asset_id —
the one field whose absence makes every beat render nothing.

These tests read the vocabularies out of aria-code and check the skill's own
documents against them, so the next rename is caught here rather than in a
failed render. They skip when aria-code is not checked out beside this repo,
because the skill still has to be publishable on its own.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ARIA_CODE = Path.home() / "Desktop" / "aria-code" / "src" / "aria_code" / "video_workflow"


def tuple_in(source: str, name: str) -> list[str]:
    """The string entries of a module-level tuple, e.g. EFFECTS = ("a", "b")."""
    match = re.search(rf"^{name} = \(([^)]*)\)", source, re.M)
    assert match, f"{name} not found"
    return re.findall(r'"([^"]+)"', match.group(1))


@unittest.skipUnless(ARIA_CODE.is_dir(), "aria-code is not checked out beside this repo")
class SkillMatchesPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan_py = (ARIA_CODE / "plan.py").read_text(encoding="utf-8")
        cls.skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cls.motion_md = (SKILL / "references" / "motion-tokens.md").read_text(encoding="utf-8")
        cls.schema = json.loads((SKILL / "assets" / "edit-plan.schema.json").read_text(encoding="utf-8"))

    def beat_property(self, name: str) -> dict:
        return self.schema["properties"]["beats"]["items"]["properties"][name]

    def test_the_schema_offers_the_sources_the_renderer_knows(self):
        self.assertEqual(
            sorted(self.beat_property("source")["enum"]),
            sorted(tuple_in(self.plan_py, "SOURCE_KINDS")),
        )

    def test_the_schema_offers_the_camera_moves_the_renderer_knows(self):
        self.assertEqual(
            sorted(self.beat_property("effect")["enum"]),
            sorted(tuple_in(self.plan_py, "EFFECTS")),
        )

    def test_the_schema_offers_the_purposes_the_renderer_knows(self):
        self.assertEqual(
            sorted(self.beat_property("purpose")["enum"]),
            sorted(tuple_in(self.plan_py, "PURPOSES")),
        )

    def test_the_schema_offers_the_aspect_ratios_the_renderer_knows(self):
        self.assertEqual(
            sorted(self.schema["properties"]["aspect_ratio"]["enum"]),
            sorted(tuple_in(self.plan_py, "ASPECT_RATIOS")),
        )

    def test_every_camera_move_is_documented(self):
        for effect in tuple_in(self.plan_py, "EFFECTS"):
            with self.subTest(effect=effect):
                self.assertIn(effect, self.motion_md)

    def test_the_generated_shot_cap_is_quoted_correctly(self):
        cap = re.search(r"^MAX_GENERATED_SECONDS = (\d+)", self.plan_py, re.M)
        assert cap, "MAX_GENERATED_SECONDS not found"
        seconds = cap.group(1)
        self.assertIn(f"{seconds} seconds", self.skill_md + self.motion_md)

    def test_the_skill_names_the_tools_that_exist(self):
        for tool in ("video_plan", "video_render"):
            self.assertIn(tool, self.skill_md)

    def test_the_skill_does_not_name_tools_that_never_existed(self):
        for ghost in ("analyze_video_script", "produce_video_from_script", "generate_video_clip"):
            self.assertNotIn(ghost, self.skill_md)

    def test_the_skill_names_the_files_the_renderer_writes(self):
        # Underscores, not hyphens; subtitles.srt, not captions.srt.
        for written in ("edit_plan.json", "assets.json", "manifest.json", "subtitles.srt"):
            with self.subTest(file=written):
                self.assertIn(written, self.skill_md)

    def test_asset_shots_must_name_their_asset(self):
        # The failure this whole reconciliation started from.
        rules = self.schema["properties"]["beats"]["items"]["allOf"]
        for source in ("asset", "animate"):
            with self.subTest(source=source):
                rule = next(r for r in rules if r["if"]["properties"]["source"]["const"] == source)
                self.assertIn("asset_id", rule["then"]["required"])
        self.assertEqual(self.beat_property("asset_id")["minLength"], 1)


if __name__ == "__main__":
    unittest.main()
