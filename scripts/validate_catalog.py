#!/usr/bin/env python3
"""Check that the catalog's four moving parts agree with each other.

`build_skill_lock.py --check` does not cover this. The lock is *derived from*
marketplace.json, so a skill that exists on disk but was never registered is
invisible to it: nothing is stale, nothing fails, and the skill silently ships
to no one. That is a real mistake with a real cost — an unregistered skill is
absent from every runtime that installs this catalog as a plugin — and it has
already happened in this repository more than once.

Checks, in the order a missing piece bites:

  1. every skill directory on disk is registered in marketplace.json
  2. every registered path actually exists on disk
  3. folder name matches the `name:` in the SKILL.md frontmatter
  4. every skill carries skill-policy.json and agents/openai.yaml
  5. every skill is listed in README.md
  6. no skill fetches and runs code from a moving source — a pipe into a
     shell, `bash <(curl …)`, `npx …@latest`, an install from a git branch,
     or a package.json lifecycle hook

Exits non-zero with every failure listed, not just the first — fixing these one
CI round-trip at a time is miserable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IGNORED = {".DS_Store", "__pycache__", ".pytest_cache"}

# Remote code that runs on install or use, from a source that can change after
# review. These are what directory maintainers such as solana.com/skills reject
# on sight (their CONTRIBUTING lists the same shapes), and an agent that
# follows a skill's instructions will run them without a second look.
# Downloading data from a moving URL — icons from unpkg@latest — is not on the
# list: nothing fetched there is executed.
REMOTE_EXECUTION = [
    (re.compile(r"(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?)\b"), "pipes a download into a shell"),
    (re.compile(r"\b(bash|sh|zsh)\s+<\(\s*(curl|wget)\b"), "runs a downloaded script"),
    (re.compile(r"\bnpx\s+(-y\s+)?\S+@latest\b"), "runs an unpinned npx package"),
    (re.compile(r"\bpip3?\s+install\s+[^\n]*git\+https?://[^\s@]+(\s|$)"), "pip-installs from a git branch"),
    (re.compile(r"\bnpm\s+(i|install)\s+[^\n]*github:[^\s#]+(\s|$)"), "npm-installs from a git branch"),
    (re.compile(r'"(preinstall|postinstall|prepare)"\s*:'), "has a package.json lifecycle script"),
]
TEXT_SUFFIXES = {".md", ".py", ".sh", ".js", ".mjs", ".ts", ".json", ".yaml", ".yml", ".toml", ".txt"}


def _frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    name = re.search(r"^name:\s*(\S+)\s*$", match.group(1), re.M)
    return name.group(1) if name else None


def validate(repo: Path = REPO) -> list[str]:
    failures: list[str] = []

    skills_dir = repo / "skills"
    on_disk = {
        d.name
        for d in skills_dir.iterdir()
        if d.is_dir() and d.name not in IGNORED and (d / "SKILL.md").is_file()
    }

    marketplace = json.loads(
        (repo / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    registered: dict[str, str] = {}
    for plugin in marketplace.get("plugins") or []:
        for relative in plugin.get("skills") or []:
            registered[Path(relative).name] = plugin["name"]

    for name in sorted(on_disk - set(registered)):
        failures.append(
            f"{name}: on disk but not registered in marketplace.json — it will "
            f"not install with any plugin"
        )
    for name in sorted(set(registered) - on_disk):
        failures.append(
            f"{name}: registered in marketplace.json but has no "
            f"skills/{name}/SKILL.md"
        )

    readme = (repo / "README.md").read_text(encoding="utf-8")

    for name in sorted(on_disk):
        folder = skills_dir / name

        declared = _frontmatter_name(folder / "SKILL.md")
        if declared is None:
            failures.append(f"{name}: SKILL.md has no parseable `name:` frontmatter")
        elif declared != name:
            failures.append(
                f"{name}: frontmatter name is {declared!r}; it must match the "
                f"folder name"
            )

        if not (folder / "skill-policy.json").is_file():
            failures.append(f"{name}: missing skill-policy.json")
        else:
            try:
                json.loads((folder / "skill-policy.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"{name}: skill-policy.json is not valid JSON ({exc})")

        descriptor = folder / "agents" / "openai.yaml"
        if not descriptor.is_file():
            failures.append(
                f"{name}: missing agents/openai.yaml — the skill is invisible in "
                f"runtimes that list skills for a human to choose from"
            )
        else:
            body = descriptor.read_text(encoding="utf-8")
            for field in ("display_name", "short_description", "default_prompt"):
                if field not in body:
                    failures.append(f"{name}: agents/openai.yaml missing {field}")
            if f"${name}" not in body:
                failures.append(
                    f"{name}: agents/openai.yaml default_prompt must reference "
                    f"${name} so the invocation is copy-pasteable"
                )

        for path in sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES
                           and not set(p.parts) & IGNORED):
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern, why in REMOTE_EXECUTION:
                match = pattern.search(text)
                if match:
                    line = text.count("\n", 0, match.start()) + 1
                    failures.append(
                        f"{name}: {path.relative_to(folder)}:{line} {why} "
                        f"({match.group(0).strip()[:60]!r}); pin it or remove it"
                    )

        if f"skills/{name})" not in readme:
            failures.append(f"{name}: not listed in README.md — undiscoverable")

        # The README's copy-pasteable `$plugin:skill` install list drifted stale
        # once already: it still showed 11 quant skills after 6 more had shipped
        # across two new plugins. A reader pastes what is printed, so a missing
        # line is a skill nobody invokes.
        # Skip when unregistered — that is already reported above, and there is
        # no plugin name to build the qualified form from.
        plugin = registered.get(name)
        if plugin:
            qualified = f"${plugin}:{name}"
            if "$quant-research-skills:" in readme and qualified not in readme:
                failures.append(
                    f"{name}: missing from the README install list (expected "
                    f"{qualified})"
                )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="show what a failure looks like, against a synthetic broken catalog",
    )
    args = parser.parse_args()

    if args.demo:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "orphan-skill").mkdir(parents=True)
            (root / "skills" / "orphan-skill" / "SKILL.md").write_text(
                "---\nname: orphan-skill\ndescription: Never registered.\n---\n",
                encoding="utf-8",
            )
            (root / ".claude-plugin").mkdir()
            (root / ".claude-plugin" / "marketplace.json").write_text(
                json.dumps({"plugins": [{"name": "demo", "skills": []}]}),
                encoding="utf-8",
            )
            (root / "README.md").write_text("# demo\n", encoding="utf-8")
            print("Synthetic catalog with one unregistered skill:")
            for failure in validate(root):
                print(f"  ✗ {failure}")
        return 0

    failures = validate()
    if failures:
        print(f"Catalog validation failed ({len(failures)} problems):")
        for failure in failures:
            print(f"  ✗ {failure}")
        return 1
    print("Catalog is consistent: disk, marketplace, policies, descriptors, README.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
