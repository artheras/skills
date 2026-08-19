#!/usr/bin/env python3
"""Validate a short-form video delivery manifest before release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VERTICAL_PLATFORMS = {
    "tiktok",
    "xiaohongshu",
    "instagram_reels",
    "youtube_shorts",
}
FEED_PLATFORMS = {"x_feed", "linkedin"}
ALLOWED_STATUSES = {"draft", "ready_for_review", "released"}
MUSIC_MODES = {"no_music", "original", "licensed", "commissioned", "user_supplied"}


def add_finding(
    findings: list[dict[str, str]], severity: str, code: str, message: str
) -> None:
    findings.append({"severity": severity, "code": code, "message": message})


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def has_errors(findings: list[dict[str, str]]) -> bool:
    return any(item["severity"] == "error" for item in findings)


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not is_non_empty_string(manifest.get("project_id")):
        add_finding(findings, "error", "project_id_missing", "project_id is required.")

    platform = manifest.get("platform")
    status = manifest.get("status")
    output = manifest.get("output")

    if platform not in VERTICAL_PLATFORMS | FEED_PLATFORMS:
        add_finding(
            findings,
            "error",
            "unsupported_platform",
            "platform must be a supported ARIA publishing destination.",
        )

    if status not in ALLOWED_STATUSES:
        add_finding(
            findings,
            "error",
            "invalid_status",
            "status must be draft, ready_for_review, or released.",
        )

    if not isinstance(output, dict):
        add_finding(findings, "error", "missing_output", "output configuration is required.")
        output = {}

    filename = output.get("filename")
    width = output.get("width")
    height = output.get("height")
    duration = output.get("duration_seconds")
    fps = output.get("fps")

    if not (is_non_empty_string(filename) and filename.lower().endswith(".mp4")):
        add_finding(findings, "error", "invalid_filename", "output must be an MP4 file.")
    if not (isinstance(width, int) and width > 0 and isinstance(height, int) and height > 0):
        add_finding(findings, "error", "invalid_dimensions", "width and height must be positive integers.")
    if not (is_number(duration) and 1 <= duration <= 180):
        add_finding(
            findings,
            "error",
            "invalid_duration",
            "duration_seconds must be between 1 and 180.",
        )
    if fps not in {24, 25, 30, 60}:
        add_finding(findings, "error", "invalid_fps", "fps must be 24, 25, 30, or 60.")

    if isinstance(width, int) and isinstance(height, int) and height > 0:
        ratio = width / height
        if platform in VERTICAL_PLATFORMS and abs(ratio - 9 / 16) > 0.02:
            add_finding(
                findings,
                "error",
                "invalid_vertical_ratio",
                "vertical destinations require a 9:16 output.",
            )
        if platform in FEED_PLATFORMS and min(abs(ratio - 16 / 9), abs(ratio - 1)) > 0.02:
            add_finding(
                findings,
                "error",
                "invalid_feed_ratio",
                "X and LinkedIn require a 16:9 or 1:1 output.",
            )

    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        add_finding(findings, "error", "missing_assets", "at least one approved asset is required.")
    elif any(
        not isinstance(asset, dict)
        or not is_non_empty_string(asset.get("source"))
        or not is_non_empty_string(asset.get("rights"))
        for asset in assets
    ):
        add_finding(
            findings,
            "error",
            "asset_provenance_incomplete",
            "every asset needs a source and rights record.",
        )

    edit_plan = manifest.get("edit_plan")
    beats = edit_plan.get("beats") if isinstance(edit_plan, dict) else None
    if not isinstance(beats, list) or not beats:
        add_finding(findings, "error", "missing_edit_plan", "at least one timed edit beat is required.")
    else:
        previous_end = 0.0
        hook_found = False
        for index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                add_finding(findings, "error", "invalid_beat", f"beat {index} must be an object.")
                continue
            start = beat.get("start_seconds")
            end = beat.get("end_seconds")
            purpose = beat.get("purpose")
            if not (
                is_number(start)
                and is_number(end)
                and start >= previous_end
                and end > start
                and (not is_number(duration) or end <= duration)
            ):
                add_finding(
                    findings,
                    "error",
                    "invalid_beat_timing",
                    f"beat {index} must have ordered timing within the output duration.",
                )
            if purpose == "hook":
                hook_found = True
                if not (is_number(end) and end <= 2):
                    add_finding(
                        findings,
                        "warning",
                        "slow_opening_hook",
                        "keep the opening hook within the first two seconds.",
                    )
            if is_number(end):
                previous_end = float(end)
        if not hook_found:
            add_finding(
                findings,
                "warning",
                "missing_hook",
                "add an explicit hook beat to improve opening clarity.",
            )

    captions = manifest.get("captions")
    if not isinstance(captions, dict) or captions.get("included") is not True:
        add_finding(findings, "error", "captions_required", "burned-in or selectable captions are required.")
    elif not is_non_empty_string(captions.get("language")):
        add_finding(findings, "error", "caption_language_missing", "caption language is required.")

    music = manifest.get("music")
    if not isinstance(music, dict):
        add_finding(findings, "error", "music_declaration_missing", "music mode must be declared.")
    else:
        mode = music.get("mode")
        if mode not in MUSIC_MODES:
            add_finding(
                findings,
                "error",
                "invalid_music_mode",
                "music mode must be no_music, original, licensed, commissioned, or user_supplied.",
            )
        elif mode == "no_music":
            if not is_non_empty_string(music.get("reason")):
                add_finding(
                    findings,
                    "error",
                    "music_reason_missing",
                    "no_music needs an editorial reason.",
                )
        else:
            track = music.get("track")
            if not isinstance(track, dict):
                add_finding(
                    findings,
                    "error",
                    "music_track_missing",
                    "music track provenance is required.",
                )
            else:
                required_track_fields = (
                    "asset_id",
                    "title",
                    "source",
                    "rights",
                    "license_proof",
                    "territory",
                    "term",
                )
                missing = [
                    field
                    for field in required_track_fields
                    if not is_non_empty_string(track.get(field))
                ]
                if missing:
                    add_finding(
                        findings,
                        "error",
                        "music_provenance_incomplete",
                        f"music track needs: {', '.join(missing)}.",
                    )
                if status == "released" and track.get("asset_status") != "cleared":
                    add_finding(
                        findings,
                        "error",
                        "music_not_cleared",
                        "released music must have a cleared asset status.",
                    )
                if status == "released" and music.get("human_approval") is not True:
                    add_finding(
                        findings,
                        "error",
                        "music_release_not_approved",
                        "released music needs human approval.",
                    )

    financial = manifest.get("financial_context")
    if isinstance(financial, dict) and financial.get("contains_financial_content") is True:
        if not is_non_empty_string(financial.get("as_of")):
            add_finding(findings, "error", "financial_as_of_missing", "financial content needs an as_of timestamp.")
        if not isinstance(financial.get("sources"), list) or not financial["sources"]:
            add_finding(findings, "error", "financial_sources_missing", "financial content needs cited sources.")
        if not is_non_empty_string(financial.get("disclosure")):
            add_finding(
                findings,
                "error",
                "financial_disclosure_missing",
                "financial content needs a risk or educational disclosure.",
            )
        if status == "released" and financial.get("human_approval") is not True:
            add_finding(
                findings,
                "error",
                "financial_release_not_approved",
                "financial content cannot be released without human approval.",
            )

    return findings


def build_demo_manifest() -> dict[str, Any]:
    return {
        "project_id": "aria-aapl-earnings-recap",
        "platform": "xiaohongshu",
        "status": "ready_for_review",
        "output": {
            "filename": "aapl-earnings-recap.mp4",
            "width": 1080,
            "height": 1920,
            "duration_seconds": 32,
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
                {"start_seconds": 2, "end_seconds": 24, "purpose": "evidence"},
                {"start_seconds": 24, "end_seconds": 32, "purpose": "close"},
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--manifest", type=Path)
    source_group.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    try:
        manifest = (
            build_demo_manifest()
            if args.demo
            else json.loads(args.manifest.read_text(encoding="utf-8"))
        )
    except (OSError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {
                    "valid": False,
                    "findings": [
                        {
                            "severity": "error",
                            "code": "manifest_unreadable",
                            "message": str(error),
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    if not isinstance(manifest, dict):
        print(
            json.dumps(
                {
                    "valid": False,
                    "findings": [
                        {
                            "severity": "error",
                            "code": "manifest_not_object",
                            "message": "manifest root must be an object.",
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    findings = validate_manifest(manifest)
    print(json.dumps({"valid": not has_errors(findings), "findings": findings}, ensure_ascii=False, indent=2))
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
