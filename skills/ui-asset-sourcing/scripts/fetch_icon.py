#!/usr/bin/env python3
"""fetch_icon.py — pulls real SVG source for a named icon from its actual
published registry, instead of an agent hand-writing `<path d="...">` data
from memory.

This is the up-front half of the failure `asset_lint.py`'s
`invented_svg_path` rule can only catch after the fact: by the time that
lint runs, the hallucinated path is already in the codebase and the icon
already renders as a blob. This script exists so there's a real fetch to
reach for instead of recalling path data — the "import by name" the
skill's Quality gate asks for actually being possible, not just stated.

Five registries, each a public URL template for the raw SVG, pinned to one
released version so the same command returns the same bytes next month:
  lucide       https://unpkg.com/lucide-static@1.66.0/icons/{name}.svg
  heroicons    https://raw.githubusercontent.com/tailwindlabs/heroicons/v2.2.0/optimized/24/outline/{name}.svg
  tabler       https://unpkg.com/@tabler/icons@3.50.0/icons/outline/{name}.svg
  phosphor     https://unpkg.com/@phosphor-icons/core@2.1.1/assets/regular/{name}.svg
  simple-icons https://unpkg.com/simple-icons@16.36.0/icons/{name}.svg   (real brand marks)

`@latest` / `master` would let whatever is published upstream tomorrow flow
straight into a user's project unreviewed. Bump a version deliberately (check
the icon paths still exist in that release) and update the tests with it.

A 404 from any of these still returns HTTP 200 with an HTML or plain-text
error body on some of these CDNs — never trust a 200 alone. `validate_svg`
checks the body actually parses as SVG (`<svg`, a real shape element) and
doesn't look like an error page, and fails loud with the resolved URL when
it doesn't, rather than silently writing garbage to disk. It also rejects
anything an inline SVG could execute or pull in: <script>, on* event
attributes, <foreignObject>, javascript: URLs, a <use> pointing outside the
document, and DOCTYPE/ENTITY declarations. A fetched icon is pasted into the
user's markup, so active content in it runs with their page's privileges.

Try it with no network:  python fetch_icon.py --demo
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import urllib.error
import urllib.request
from typing import Callable, Dict, List, Optional, Tuple

# Pinned releases — verified to contain the icon paths below (npm tarballs
# for the unpkg packages, the v2.2.0 tag for heroicons).
_VERSIONS: Dict[str, str] = {
    "lucide": "1.66.0",
    "heroicons": "v2.2.0",
    "tabler": "3.50.0",
    "phosphor": "2.1.1",
    "simple-icons": "16.36.0",
}

_REGISTRIES: Dict[str, str] = {
    "lucide": f"https://unpkg.com/lucide-static@{_VERSIONS['lucide']}/icons/{{name}}.svg",
    "heroicons": "https://raw.githubusercontent.com/tailwindlabs/heroicons/"
                 f"{_VERSIONS['heroicons']}/optimized/24/outline/{{name}}.svg",
    "tabler": f"https://unpkg.com/@tabler/icons@{_VERSIONS['tabler']}/icons/outline/{{name}}.svg",
    "phosphor": f"https://unpkg.com/@phosphor-icons/core@{_VERSIONS['phosphor']}/assets/regular/{{name}}.svg",
    "simple-icons": f"https://unpkg.com/simple-icons@{_VERSIONS['simple-icons']}/icons/{{name}}.svg",
}

_USER_AGENT = "aria-skills-ui-asset-sourcing/1.0 (+fetch_icon.py)"
_DEFAULT_TIMEOUT = 10.0

_SHAPE_TAGS = ("<path", "<circle", "<rect", "<polygon", "<polyline", "<ellipse", "<line")
_ERROR_PAGE_MARKERS = ("<html", "cannot get", "404", "not found", "error code")

_TAG_RE = re.compile(r"<[^>]*>", re.S)
_EVENT_ATTR_RE = re.compile(r"[\s/\"']on[a-z]+\s*=", re.I)
_USE_HREF_RE = re.compile(r"""(?:xlink:)?href\s*=\s*["']?\s*([^"'\s>]*)""", re.I)


def _active_content(content: str) -> Optional[str]:
    """Why this SVG is unsafe to inline, or None. Conservative on purpose:
    no icon from these five registries needs any of these constructs."""
    low = content.lower()
    if re.search(r"<\s*script\b", low):
        return "contains a <script> element"
    if re.search(r"<\s*foreignobject\b", low):
        return "contains a <foreignObject> element"
    if re.search(r"<!\s*(doctype|entity)\b", low):
        return "contains a DOCTYPE/ENTITY declaration"
    if re.search(r"javascript\s*:", low):
        return "contains a javascript: URL"
    for tag in _TAG_RE.findall(content):
        if _EVENT_ATTR_RE.search(tag):
            return "has an on* event-handler attribute"
        if re.match(r"<\s*use\b", tag, re.I):
            for ref in _USE_HREF_RE.findall(tag):
                if not ref.startswith("#"):
                    return f"has a <use> referencing outside the document ({ref[:60]})"
    return None


# Simple Icons slugs are NOT kebab-case like the other four registries — they
# concatenate words with no separator and spell out certain punctuation
# ("Node.js" -> "nodedotjs", "C++" -> "cplusplus", ".NET" -> "dotnet"). Verified
# live against unpkg for americanexpress/adobephotoshop/visualstudiocode/
# nodedotjs/cocacola. This table covers the common cases, not necessarily
# every brand's exact slug — a miss fails loud via the 404/validate_svg path
# below rather than silently writing the wrong icon.
_SIMPLE_ICONS_CHAR_MAP = {"+": "plus", "#": "sharp", ".": "dot", "&": "and"}


def _kebab_slug(name: str) -> str:
    return name.strip().lower().replace("_", "-").replace(" ", "-")


def _simple_icons_slug(name: str) -> str:
    s = name.strip().lower()
    for ch, word in _SIMPLE_ICONS_CHAR_MAP.items():
        s = s.replace(ch, word)
    return re.sub(r"[^a-z0-9]", "", s)


def resolve_url(library: str, name: str) -> str:
    if library not in _REGISTRIES:
        raise ValueError(
            f"unknown library '{library}' — available: {', '.join(sorted(_REGISTRIES))}"
        )
    normalized = _simple_icons_slug(name) if library == "simple-icons" else _kebab_slug(name)
    return _REGISTRIES[library].format(name=normalized)


def validate_svg(content: str) -> Tuple[bool, str]:
    """Real SVG, or an error page / empty body wearing a 200 status?
    Deliberately conservative — reject anything that isn't clearly valid
    rather than accept anything that isn't clearly invalid."""
    if not content or not content.strip():
        return False, "empty response body"
    low = content.lower()
    if "<svg" not in low:
        return False, "response does not contain an <svg> tag"
    if not any(tag in low for tag in _SHAPE_TAGS):
        return False, "response has an <svg> tag but no recognized shape element " \
                       f"({', '.join(t.strip('<') for t in _SHAPE_TAGS)})"
    if any(marker in low for marker in _ERROR_PAGE_MARKERS) and "<path" not in low:
        return False, "response looks like an error page, not an icon"
    unsafe = _active_content(content)
    if unsafe:
        return False, f"unsafe SVG: {unsafe}"
    return True, "ok"


def fetch_raw(url: str, *, timeout: float = _DEFAULT_TIMEOUT) -> str:
    """The one function that actually touches the network — kept tiny and
    separate so tests and --demo can substitute a fake fetcher instead of
    requiring a live connection."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_icon(
    library: str, name: str, *,
    fetch_fn: Callable[[str], str] = fetch_raw,
) -> Dict[str, object]:
    """Resolves, fetches, and validates one icon. Raises ValueError for an
    unknown library (a usage error) but returns a result dict with
    ok=False for a fetch/validation failure (an expected runtime outcome,
    not a bug) — callers branch on `ok`, not on exceptions, for the latter."""
    url = resolve_url(library, name)
    try:
        content = fetch_fn(url)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"ok": False, "library": library, "name": name, "url": url,
                "reason": f"fetch failed: {exc}", "content": None}

    ok, reason = validate_svg(content)
    result: Dict[str, object] = {
        "ok": ok, "library": library, "name": name, "url": url, "reason": reason,
        "content": content if ok else None,
    }
    if ok:
        result["sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return result


# ───────────────────────────── demo ──────────────────────────────────────────

def _fake_fetch_valid(url: str) -> str:
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'


def _fake_fetch_404_page(url: str) -> str:
    return "<html><body>Cannot GET " + url + "</body></html>"


def _fake_fetch_empty(url: str) -> str:
    return ""


def demo() -> int:
    print("=" * 72)
    print("DEMO — real fetch/validate logic, network replaced with fixed responses")
    print("=" * 72)

    good = fetch_icon("lucide", "arrow-right", fetch_fn=_fake_fetch_valid)
    print(f"\n[valid SVG response]\n  url={good['url']}\n  ok={good['ok']}  "
          f"sha256={good.get('sha256')}")

    error_page = fetch_icon("lucide", "definitely-not-a-real-icon-xyz", fetch_fn=_fake_fetch_404_page)
    print(f"\n[404-page-disguised-as-200 response]\n  url={error_page['url']}\n  "
          f"ok={error_page['ok']}  reason={error_page['reason']}")

    empty = fetch_icon("heroicons", "arrow-right", fetch_fn=_fake_fetch_empty)
    print(f"\n[empty body response]\n  ok={empty['ok']}  reason={empty['reason']}")

    try:
        resolve_url("not-a-real-library", "arrow-right")
        unknown_library_raised = False
    except ValueError as exc:
        unknown_library_raised = True
        print(f"\n[unknown library]\n  raised ValueError: {exc}")

    ok = (
        good["ok"] is True
        and good.get("sha256") is not None
        and error_page["ok"] is False
        and empty["ok"] is False
        and unknown_library_raised
    )
    print()
    print("=" * 72)
    print("demo OK — valid SVG accepted, error page and empty body rejected, "
          "unknown library fails loud" if ok else "demo UNEXPECTED — check implementation")
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Fetch a real icon SVG by name from its published registry")
    ap.add_argument("--library", choices=sorted(_REGISTRIES), help="icon registry")
    ap.add_argument("--name", help="icon name, e.g. 'arrow-right'")
    ap.add_argument("--out", help="write SVG here instead of stdout")
    ap.add_argument("--list-libraries", action="store_true")
    ap.add_argument("--timeout", type=float, default=_DEFAULT_TIMEOUT)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)

    if args.demo:
        return demo()

    if args.list_libraries:
        for lib, template in sorted(_REGISTRIES.items()):
            print(f"{lib}: {template}")
        return 0

    if not args.library or not args.name:
        ap.error("--demo, --list-libraries, or --library/--name together, is required")
        return 2

    result = fetch_icon(
        args.library, args.name,
        fetch_fn=lambda url: fetch_raw(url, timeout=args.timeout),
    )
    if not result["ok"]:
        print(f"FAIL: {result['reason']}\n  url={result['url']}", file=sys.stderr)
        return 1

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(result["content"])
        print(f"wrote {args.out} (sha256={result['sha256']}, source={result['url']})")
    else:
        print(result["content"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
