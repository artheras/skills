#!/usr/bin/env python3
"""Validate a rights-safe ARIA music cue manifest before release."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_MODES = {"no_music", "original", "licensed", "commissioned", "user_supplied"}
ALLOWED_STATUSES = {"draft", "ready_for_review", "released"}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "assets" / "aria-cue-catalog.json"


def add_finding(findings: list[dict[str, str]], level: str, code: str, message: str) -> None:
    findings.append({"level": level, "code": code, "message": message})


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def has_errors(findings: list[dict[str, str]]) -> bool:
    return any(finding["level"] == "error" for finding in findings)


def load_catalog_ids(path: Path) -> set[str]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    cues = catalog.get("cues", []) if isinstance(catalog, dict) else []
    return {
        cue.get("id")
        for cue in cues
        if isinstance(cue, dict) and is_non_empty_string(cue.get("id"))
    }


def validate_manifest(manifest: dict[str, Any], catalog_ids: set[str]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not is_non_empty_string(manifest.get("project_id")):
        add_finding(findings, "error", "project_id_missing", "project_id is required.")

    status = manifest.get("status")
    if status not in ALLOWED_STATUSES:
        add_finding(findings, "error", "status_invalid", "status must be draft, ready_for_review, or released.")

    usage = manifest.get("usage")
    if not isinstance(usage, dict):
        add_finding(findings, "error", "usage_missing", "usage must declare how music is used.")
    else:
        mode = usage.get("mode")
        if mode not in ALLOWED_MODES:
            add_finding(findings, "error", "usage_mode_invalid", "usage.mode is not supported.")
        elif mode == "no_music":
            if not is_non_empty_string(usage.get("reason")):
                add_finding(findings, "error", "no_music_reason_missing", "no_music requires a concise editorial reason.")
        else:
            cue_id = usage.get("cue_id")
            if is_non_empty_string(cue_id) and cue_id not in catalog_ids:
                add_finding(findings, "error", "cue_id_invalid", "usage.cue_id is not present in the approved cue catalog.")
            track = manifest.get("track")
            if not isinstance(track, dict):
                add_finding(findings, "error", "track_missing", "Non-silent music requires a track rights record.")
            else:
                required_fields = ("asset_id", "title", "source", "rights", "license_proof", "territory", "term")
                if not all(is_non_empty_string(track.get(field)) for field in required_fields):
                    add_finding(findings, "error", "track_provenance_incomplete", "Track source, rights, proof, territory, and term are required.")
                if status == "released" and track.get("asset_status") != "cleared":
                    add_finding(findings, "error", "track_not_cleared", "Released music must have asset_status set to cleared.")
                if status == "released" and manifest.get("human_approval") is not True:
                    add_finding(findings, "error", "music_release_not_approved", "Released music requires explicit human approval.")

    mix = manifest.get("mix")
    if not isinstance(mix, dict):
        add_finding(findings, "error", "mix_missing", "mix settings are required.")
    else:
        target_lufs = mix.get("target_lufs")
        if not is_number(target_lufs) or not -24 <= float(target_lufs) <= -8:
            add_finding(findings, "error", "mix_target_invalid", "target_lufs must be between -24 and -8.")
        ducking_db = mix.get("ducking_db")
        if not is_number(ducking_db) or not 0 <= float(ducking_db) <= 18:
            add_finding(findings, "error", "mix_ducking_invalid", "ducking_db must be between 0 and 18.")
        peak = mix.get("true_peak_dbtp")
        if peak is not None and (not is_number(peak) or float(peak) > -0.1):
            add_finding(findings, "error", "mix_true_peak_invalid", "true_peak_dbtp must be at or below -0.1.")

    financial = manifest.get("financial_context")
    if isinstance(financial, dict) and financial.get("contains_financial_content") is True:
        if not is_non_empty_string(financial.get("as_of")):
            add_finding(findings, "error", "financial_as_of_missing", "Financial content requires an as_of timestamp.")
        if not isinstance(financial.get("sources"), list) or not financial["sources"]:
            add_finding(findings, "error", "financial_sources_missing", "Financial content requires at least one source.")
        if not is_non_empty_string(financial.get("disclosure")):
            add_finding(findings, "error", "financial_disclosure_missing", "Financial content requires a disclosure.")
        if status == "released" and manifest.get("human_approval") is not True:
            add_finding(findings, "error", "financial_release_not_approved", "Released financial content requires human approval.")

    return findings


def build_demo_manifest() -> dict[str, Any]:
    return {
        "project_id": "demo-harbor-recap",
        "status": "ready_for_review",
        "usage": {
            "mode": "no_music",
            "reason": "Voice-led harbor recap; a soundtrack would reduce source clarity."
        },
        "mix": {"target_lufs": -16, "ducking_db": 8, "true_peak_dbtp": -1},
        "financial_context": {"contains_financial_content": False}
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="Path to a music cue manifest JSON file.")
    source.add_argument("--demo", action="store_true", help="Validate the bundled safe no-music example.")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="Path to the approved cue catalog.")
    args = parser.parse_args()

    try:
        manifest = build_demo_manifest() if args.demo else json.loads(args.manifest.read_text(encoding="utf-8"))
        catalog_ids = load_catalog_ids(args.catalog)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "findings": [{"level": "error", "code": "input_invalid", "message": str(error)}]}, ensure_ascii=False, indent=2))
        return 1

    if not isinstance(manifest, dict):
        print(json.dumps({"valid": False, "findings": [{"level": "error", "code": "manifest_invalid", "message": "Manifest root must be an object."}]}, ensure_ascii=False, indent=2))
        return 1

    findings = validate_manifest(manifest, catalog_ids)
    print(json.dumps({"valid": not has_errors(findings), "findings": findings}, ensure_ascii=False, indent=2))
    return 1 if has_errors(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
