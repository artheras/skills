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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "findings": [{"severity": "error", "code": "manifest_unreadable", "message": str(error)}]}, ensure_ascii=False, indent=2))
        return 1

    if not isinstance(manifest, dict):
        print(json.dumps({"valid": False, "findings": [{"severity": "error", "code": "manifest_not_object", "message": "manifest root must be an object."}]}, ensure_ascii=False, indent=2))
        return 1

    findings = validate_manifest(manifest)
    print(json.dumps({"valid": not has_errors(findings), "findings": findings}, ensure_ascii=False, indent=2))
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
