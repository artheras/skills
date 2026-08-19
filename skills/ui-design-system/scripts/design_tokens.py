#!/usr/bin/env python3
"""design-tokens.json scaffolder + validator — objective checks only, no taste.

The user owns the file; this script only (a) prints a fillable skeleton and
(b) validates a filled one against things that are true or false regardless of
aesthetics: schema completeness, WCAG contrast, monotonic radius/spacing scales.

Usage:
    python design_tokens.py --template            # print annotated skeleton
    python design_tokens.py --validate tokens.json
    python design_tokens.py --demo                # self-contained smoke test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "aria.design-tokens.v1"
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

TEMPLATE = {
    "schema_version": SCHEMA_VERSION,
    "name": "<your system name>",
    "appearance": "light-dark",
    "conventions": {"emoji_icons": "forbid"},
    "color": {
        "canvas": {"light": "#FFFFFF", "dark": "#000000"},
        "surface": {"light": "#FFFFFF", "dark": "#111111"},
        "textPrimary": {"light": "#111111", "dark": "#FFFFFF"},
        "textSecondary": {"light": "#555555", "dark": "#AAAAAA"},
        "border": {"light": "#E5E5E5", "dark": "#2A2A2A"},
        "accent": {"light": "#0055FF", "dark": "#4488FF"},
    },
    "radius": {"chip": 6, "control": 8, "card": 12, "sheet": 16, "hero": 20},
    "spacing": {"base": 4, "steps": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32}},
    "type": {
        "title": {"size": 22, "weight": 600, "mono": False},
        "body": {"size": 15, "weight": 400, "mono": False},
        "caption": {"size": 11, "weight": 400, "mono": False},
    },
    "stroke": {"hairline": 0.5, "border": 1},
    # Motion lives in the same file as color/spacing so animation stays part of
    # the design system instead of being reinvented per component. Owned by the
    # web-motion-design skill; see its references/motion_tokens.md. Optional —
    # a token file with no "motion" key stays valid.
    "motion": {
        "duration": {"instant": 100, "fast": 150, "base": 200, "slow": 300, "deliberate": 400},
        "easing": {
            "enter": [0, 0, 0.2, 1],
            "exit": [0.4, 0, 1, 1],
            "inOut": [0.4, 0, 0.2, 1],
        },
        "reduced_motion": "reduce",
    },
    "contrast_pairs": [
        {"text": "textPrimary", "on": "canvas", "min": 4.5},
        {"text": "textSecondary", "on": "canvas", "min": 4.5},
    ],
}


# ─────────────────────────── WCAG contrast ──────────────────────────────────
def _channel(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ─────────────────────────── validation ─────────────────────────────────────
def _color_values(spec, appearance: str) -> list[str]:
    """Return the hex value(s) for one color entry given the appearance mode."""
    if appearance == "single":
        return [spec] if isinstance(spec, str) else []
    if isinstance(spec, dict):
        return [v for v in (spec.get("light"), spec.get("dark")) if isinstance(v, str)]
    return []


def validate(tokens: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if tokens.get("schema_version") != SCHEMA_VERSION:
        warnings.append(f"schema_version is not {SCHEMA_VERSION!r}")
    for req in ("name", "appearance", "color"):
        if req not in tokens:
            errors.append(f"missing required field: {req}")

    appearance = tokens.get("appearance")
    if appearance not in ("light-dark", "single"):
        errors.append("appearance must be 'light-dark' or 'single'")
        appearance = None

    # colors: every value a valid hex, and shape matches appearance
    colors = tokens.get("color", {})
    for name, spec in colors.items():
        if appearance == "single":
            if not (isinstance(spec, str) and _HEX_RE.match(spec)):
                errors.append(f"color.{name}: expected #RRGGBB hex for single appearance")
        elif appearance == "light-dark":
            if not (isinstance(spec, dict) and {"light", "dark"} <= set(spec)):
                errors.append(f"color.{name}: expected {{light, dark}} for light-dark appearance")
            else:
                for mode in ("light", "dark"):
                    if not _HEX_RE.match(str(spec[mode])):
                        errors.append(f"color.{name}.{mode}: not a #RRGGBB hex")

    # radius: strictly increasing distinct tiers
    radius = tokens.get("radius", {})
    if radius:
        vals = list(radius.values())
        srt = sorted(vals)
        if srt != sorted(set(vals)) or any(a == b for a, b in zip(srt, srt[1:])):
            errors.append("radius tiers must be distinct (no two the same value)")

    # spacing: steps are base multiples, strictly increasing
    spacing = tokens.get("spacing", {})
    if spacing:
        base = spacing.get("base")
        steps = spacing.get("steps", {})
        if not isinstance(base, (int, float)) or base <= 0:
            errors.append("spacing.base must be a positive number")
        elif steps:
            for k, v in steps.items():
                if not isinstance(v, (int, float)) or v % base != 0:
                    errors.append(f"spacing.steps.{k}={v} is not a multiple of base {base}")
            svals = list(steps.values())
            if sorted(svals) != sorted(set(svals)):
                errors.append("spacing.steps must be distinct")

    # motion: duration tiers in ms, easing as 4-point cubic-bezier
    motion = tokens.get("motion", {})
    if motion:
        if not isinstance(motion, dict):
            errors.append("motion must be an object")
            motion = {}

        durations = motion.get("duration", {}) or {}
        for k, v in durations.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0:
                errors.append(f"motion.duration.{k}={v!r} must be a positive number (milliseconds)")
            elif v < 1:
                # 0.3 in a ms field is almost always "0.3 seconds" written into the
                # wrong unit — it validates as a number but produces a 0.3ms
                # animation, i.e. invisible. Catch it rather than let it ship.
                errors.append(
                    f"motion.duration.{k}={v} is under 1ms — looks like seconds in a "
                    f"milliseconds field (did you mean {int(v * 1000)}?)"
                )
            elif v > 1000:
                warnings.append(
                    f"motion.duration.{k}={v}ms is over 1s — fine for a loading "
                    f"illustration, too slow for a UI transition"
                )
        dvals = [v for v in durations.values() if isinstance(v, (int, float))]
        if dvals and sorted(dvals) != sorted(set(dvals)):
            errors.append("motion.duration tiers must be distinct (no two the same value)")

        easings = motion.get("easing", {}) or {}
        for k, v in easings.items():
            if not (isinstance(v, list) and len(v) == 4 and
                    all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in v)):
                errors.append(f"motion.easing.{k} must be 4 numbers [x1,y1,x2,y2]")
                continue
            # Only the time axis (x) is clamped by the CSS spec. y may exceed
            # [0,1] — that is how overshoot/anticipation curves are expressed.
            for idx in (0, 2):
                if not 0 <= v[idx] <= 1:
                    errors.append(
                        f"motion.easing.{k}[{idx}]={v[idx]} out of range — cubic-bezier "
                        f"x control points must be within [0,1]"
                    )

        reduced = motion.get("reduced_motion")
        if reduced is not None and reduced not in ("reduce", "disable"):
            errors.append("motion.reduced_motion must be 'reduce' or 'disable'")

    # contrast_pairs: WCAG in every declared appearance
    contrast: list[dict] = []
    for pair in tokens.get("contrast_pairs", []) or []:
        tname, oname = pair.get("text"), pair.get("on")
        minv = pair.get("min", 4.5)
        if tname not in colors or oname not in colors:
            warnings.append(f"contrast_pair references unknown color: {tname} on {oname}")
            continue
        modes = ["single"] if appearance == "single" else ["light", "dark"]
        for mode in modes:
            if appearance == "single":
                tv = colors[tname] if isinstance(colors[tname], str) else None
                ov = colors[oname] if isinstance(colors[oname], str) else None
            else:
                tv = colors[tname].get(mode) if isinstance(colors[tname], dict) else None
                ov = colors[oname].get(mode) if isinstance(colors[oname], dict) else None
            if not (tv and ov and _HEX_RE.match(tv) and _HEX_RE.match(ov)):
                continue
            ratio = contrast_ratio(tv, ov)
            rec = {"text": tname, "on": oname, "mode": mode,
                   "ratio": round(ratio, 2), "min": minv, "pass": ratio >= minv}
            contrast.append(rec)
            if not rec["pass"]:
                errors.append(
                    f"contrast {tname} on {oname} ({mode}) = {ratio:.2f} < {minv} (WCAG fail)")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "contrast": contrast,
    }


def _print_report(report: dict) -> None:
    if report["valid"]:
        print("  tokens valid")
    else:
        print(f"  INVALID — {len(report['errors'])} error(s)")
    for e in report["errors"]:
        print(f"    error: {e}")
    for w in report["warnings"]:
        print(f"    warn:  {w}")
    if report["contrast"]:
        print("  contrast:")
        for c in report["contrast"]:
            flag = "ok" if c["pass"] else "FAIL"
            print(f"    {c['text']} on {c['on']} ({c['mode']}): {c['ratio']} [{flag}]")


# ─────────────────────────── extract ───────────────────────────────────────
# "Extract before invent": harvest the colors/radii a codebase already uses,
# cluster near-duplicates, and emit a tokens DRAFT for the user to name and
# prune. Regexes are inlined here (not shared with design_lint) so each script
# stays independently readable — the same house style as factor_audit vs
# factor_evaluate each inlining their own stats.
_X_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
_X_SWIFT_RGB_RE = re.compile(r"Color\(\s*red:\s*([\d.]+),\s*green:\s*([\d.]+),\s*blue:\s*([\d.]+)")
_X_CSS_RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")
_X_RADIUS_RE = re.compile(r"(?:cornerRadius|border-?[Rr]adius)\s*:?\s*\(?\s*(\d+(?:\.\d+)?)")
_X_SCAN_SUFFIXES = {".swift", ".css", ".scss", ".tsx", ".jsx", ".ts", ".js",
                    ".dart", ".vue", ".html"}
CLUSTER_TOLERANCE = 6.0  # RGB distance under which two colors fold into one token


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _color_distance(h1: str, h2: str) -> float:
    a, b = _hex_to_rgb(h1), _hex_to_rgb(h2)
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _rgb01_to_hex(r: str, g: str, b: str) -> str:
    return "#" + "".join(f"{round(float(c) * 255):02x}" for c in (r, g, b))


def _rgb255_to_hex(r: str, g: str, b: str) -> str:
    return "#" + "".join(f"{max(0, min(255, int(c))):02x}" for c in (r, g, b))


def _cluster_colors(counts: dict[str, int], tol: float) -> list[tuple[str, int]]:
    """Fold near-duplicate hexes into their most-frequent representative."""
    reps: list[list] = []  # [representative_hex, total_count]
    for hx, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        for rep in reps:
            if _color_distance(hx, rep[0]) <= tol:
                rep[1] += cnt
                break
        else:
            reps.append([hx, cnt])
    reps.sort(key=lambda r: (-r[1], r[0]))
    return [(r[0], r[1]) for r in reps]


def extract(paths: list[str], tol: float = CLUSTER_TOLERANCE) -> dict:
    """Scan code for color/radius literals -> a tokens DRAFT (single appearance)."""
    color_counts: dict[str, int] = {}
    radius_counts: dict[str, int] = {}
    files_scanned = 0

    def _note_color(hx: str) -> None:
        hx = "#" + hx.lstrip("#").lower()
        color_counts[hx] = color_counts.get(hx, 0) + 1

    for p in paths:
        root = Path(p)
        files = ([root] if root.is_file()
                 else sorted(f for f in root.rglob("*") if f.suffix in _X_SCAN_SUFFIXES))
        for f in files:
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            files_scanned += 1
            for raw in text.splitlines():
                line = raw.split("//", 1)[0]
                for m in _X_HEX_RE.finditer(line):
                    _note_color(m.group(0))
                for m in _X_SWIFT_RGB_RE.finditer(line):
                    _note_color(_rgb01_to_hex(*m.groups()))
                for m in _X_CSS_RGB_RE.finditer(line):
                    _note_color(_rgb255_to_hex(*m.groups()))
                for m in _X_RADIUS_RE.finditer(line):
                    v = m.group(1)
                    radius_counts[v] = radius_counts.get(v, 0) + 1

    clustered = _cluster_colors(color_counts, tol)
    colors = {f"color_{i + 1}": hx for i, (hx, _cnt) in enumerate(clustered)}
    radii = {}
    for i, (val, _cnt) in enumerate(sorted(
            radius_counts.items(), key=lambda kv: (-kv[1], float(kv[0])))):
        num = float(val)
        radii[f"radius_{i + 1}"] = int(num) if num.is_integer() else num

    draft = {
        "schema_version": SCHEMA_VERSION,
        "name": "<name your system>",
        "appearance": "single",
        "conventions": {"emoji_icons": "forbid"},
        "color": colors,
        "radius": radii,
        "_draft_note": (
            f"Extracted from {files_scanned} file(s). RENAME color_N/radius_N "
            "semantically, set appearance (light-dark?), and prune duplicates "
            "before use. Re-run --validate after editing."),
    }
    return draft


def _demo_extract() -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "a.css").write_text(
            "a { color: #2F6BFF; }\n.b { color: #2f6cff; }\n"   # near-duplicate → one cluster
            ".c { border-radius: 12px; }\n", encoding="utf-8")
        (tmp / "b.swift").write_text(
            "Color(red: 0.114, green: 0.725, blue: 0.329)\n"    # #1db954
            ".cornerRadius(12)\n", encoding="utf-8")
        draft = extract([str(tmp)])
        print("=== demo: extract from a mixed CSS+Swift dir ===")
        print(json.dumps({k: draft[k] for k in ("color", "radius")}, indent=2))
        # the two near-blues fold into a single token; the green is its own
        assert len(draft["color"]) == 2, draft["color"]
        assert draft["radius"] == {"radius_1": 12}, draft["radius"]
        # the draft is structurally validatable once named (single appearance)
        named = json.loads(json.dumps(draft))
        named["name"] = "X"
        assert validate(named)["valid"], validate(named)["errors"]
        print("  extract demo assertions passed")


def _demo() -> int:
    _demo_extract()
    print()
    good = json.loads(json.dumps(TEMPLATE))
    good["name"] = "DemoGood"
    rep = validate(good)
    print("=== demo: template (should be valid) ===")
    _print_report(rep)
    assert rep["valid"], rep["errors"]

    bad = json.loads(json.dumps(TEMPLATE))
    bad["name"] = "DemoBad"
    bad["color"]["textSecondary"] = {"light": "#BBBBBB", "dark": "#AAAAAA"}  # low contrast on white
    bad["radius"]["control"] = 6  # collides with chip=6
    bad["spacing"]["steps"]["odd"] = 5  # not a multiple of 8
    rep2 = validate(bad)
    print("\n=== demo: deliberately broken (should be invalid) ===")
    _print_report(rep2)
    assert not rep2["valid"]
    kinds = " ".join(rep2["errors"])
    assert "contrast" in kinds and "radius" in kinds and "multiple" in kinds
    print("\n  demo assertions passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="design-tokens.json scaffolder + validator")
    ap.add_argument("--template", action="store_true", help="print fillable skeleton")
    ap.add_argument("--validate", metavar="FILE", help="validate a tokens file")
    ap.add_argument("--extract", nargs="+", metavar="PATH",
                    help="scan code files/dirs and emit a tokens DRAFT to stdout")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)

    if args.demo:
        return _demo()
    if args.template:
        print(json.dumps(TEMPLATE, indent=2))
        return 0
    if args.extract:
        print(json.dumps(extract(args.extract), indent=2))
        return 0
    if args.validate:
        try:
            tokens = json.loads(Path(args.validate).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"  cannot read tokens: {e}")
            return 1
        report = validate(tokens)
        _print_report(report)
        return 0 if report["valid"] else 1

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
