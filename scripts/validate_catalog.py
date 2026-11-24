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
  7. SKILL.md stays inside Aria Code's loader limits — starts with "---\n"
     (no BOM), LF line endings (a CRLF copy fails the lock digest), at most
     20,000 characters, a name matching
     ^[a-z0-9][a-z0-9-]{0,63}$, a non-empty description and body. The loader
     drops a skill that breaks any of these without a word.
  8. every `allowed_tools` entry is a tool Aria actually has
     (scripts/aria_known_tools.json). Aria narrows the model's tool schema to
     core file tools plus the active skills' allowed_tools, so a misspelt
     name does not fail — it just removes the tool the skill needed.
  9. quoted trigger phrases in the description are specific enough. The
     loader activates a skill on any quoted phrase found as a substring of
     the user's message, so "VaR" fires on "various" and "done" on almost
     anything. Each phrase must be at least 5 characters (4 if it contains
     CJK), not a single bare English word, not split by a line fold between
     CJK characters, and not contained in another skill's phrase.
 10. every skill with a scripts/ directory has a CI job in
     .github/workflows/test.yml, and lists run_command in a non-empty
     allowed_tools unless its scripts policy is "execution": "none"

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
# review. Skill directories reject these on sight as supply-chain risks, and an
# agent that follows a skill's instructions will run them without a second
# look.
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
# Mirrors aria-code src/aria_code/packages/aria_skills/loader.py.
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
MAX_SKILL_CHARS = 20_000
QUOTED_RE = re.compile(r'"([^"]+)"|“([^”]+)”|\'([^\']+)\'')
CJK_RE = re.compile(r"[\u3400-\u9fff]")
MIN_PHRASE_CHARS = 5
MIN_CJK_PHRASE_CHARS = 4
MCP_QUALIFIED_RE = re.compile(r"^mcp__[A-Za-z0-9_.-]+__[A-Za-z0-9_.-]+$")
KNOWN_TOOLS_FILE = Path(__file__).resolve().parent / "aria_known_tools.json"

TEXT_SUFFIXES = {".md", ".py", ".sh", ".js", ".mjs", ".ts", ".json", ".yaml", ".yml", ".toml", ".txt"}


def _frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    name = re.search(r"^name:\s*(\S+)\s*$", match.group(1), re.M)
    return name.group(1) if name else None


def _frontmatter_value(lines: list[str], key: str) -> str:
    """Same parsing as aria-code's loader, including `>-` folded blocks."""
    prefix = f"{key}:"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        value = line[len(prefix):].strip()
        if value not in {">", ">-", "|", "|-"}:
            return value.strip("\"'")
        folded = value.startswith(">")
        parts: list[str] = []
        for continuation in lines[index + 1:]:
            if continuation and not continuation[0].isspace():
                break
            stripped = continuation.strip()
            if stripped:
                parts.append(stripped)
        return (" " if folded else "\n").join(parts)
    return ""


def _loader_failures(name: str, text: str) -> tuple[list[str], str]:
    """Return (failures, description) for the loader's silent-drop rules."""
    failures: list[str] = []
    if "\r\n" in text:
        # The loader reads with universal newlines, so CRLF parses — but the
        # integrity lock hashes raw bytes, so a CRLF copy never matches it and
        # the skill can no longer activate automatically.
        failures.append(
            f"{name}: SKILL.md has CRLF line endings; a CRLF checkout fails the "
            f"skills.lock digest check (see .gitattributes)"
        )
        text = text.replace("\r\n", "\n")
    if not text.startswith("---\n"):
        failures.append(f"{name}: SKILL.md must start with '---\\n' or the loader skips it")
        return failures, ""
    if len(text) > MAX_SKILL_CHARS:
        failures.append(
            f"{name}: SKILL.md is {len(text):,} characters; the loader skips files over "
            f"{MAX_SKILL_CHARS:,} — move material into references/"
        )
    end = text.find("\n---\n", 4)
    if end < 0:
        failures.append(f"{name}: SKILL.md frontmatter is not closed by '---'")
        return failures, ""
    lines = text[4:end].splitlines()
    declared = _frontmatter_value(lines, "name")
    if not NAME_RE.fullmatch(declared):
        failures.append(f"{name}: name {declared!r} does not match {NAME_RE.pattern}")
    description = _frontmatter_value(lines, "description")
    if not description:
        failures.append(f"{name}: empty description — the loader skips the skill")
    if not text[end + 5:].strip():
        failures.append(f"{name}: SKILL.md has no body — the loader skips the skill")
    return failures, description


def quoted_phrases(description: str) -> list[str]:
    return [
        next(group for group in match.groups() if group is not None).strip().lower()
        for match in QUOTED_RE.finditer(description)
    ]


def _phrase_problem(phrase: str) -> str | None:
    has_cjk = bool(CJK_RE.search(phrase))
    minimum = MIN_CJK_PHRASE_CHARS if has_cjk else MIN_PHRASE_CHARS
    if len(phrase) < minimum:
        return f"is shorter than {minimum} characters"
    if not has_cjk and re.fullmatch(r"[a-z]+[.,!?]?", phrase):
        return "is a single common word"
    if re.search(r"[\u3400-\u9fff] [\u3400-\u9fff]", phrase):
        return "has a space between CJK characters (a line fold inside the quotes?)"
    return None


def load_known_tools(path: Path = KNOWN_TOOLS_FILE) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        str(tool)
        for key, tools in payload.items()
        if not key.startswith("_")
        for tool in tools
    }


def validate(repo: Path = REPO, known_tools: set[str] | None = None) -> list[str]:
    failures: list[str] = []
    if known_tools is None:
        known_tools = load_known_tools()
    workflow_path = repo / ".github" / "workflows" / "test.yml"
    workflow = workflow_path.read_text(encoding="utf-8") if workflow_path.is_file() else ""
    phrases_by_skill: dict[str, list[str]] = {}

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

        skill_text = (folder / "SKILL.md").read_bytes().decode("utf-8", errors="replace")
        loader_failures, description = _loader_failures(name, skill_text)
        failures.extend(loader_failures)
        phrases = quoted_phrases(description)
        phrases_by_skill[name] = phrases
        for phrase in phrases:
            problem = _phrase_problem(phrase)
            if problem:
                failures.append(
                    f"{name}: quoted trigger phrase {phrase!r} {problem} — the loader "
                    f"activates on it as a substring of any message; reword or unquote it"
                )

        for match in QUOTED_RE.finditer(description):
            if match.group(3) is not None and match.start() and description[match.start() - 1].isalnum():
                failures.append(
                    f"{name}: an ASCII apostrophe opens the accidental trigger phrase "
                    f"{match.group(3)!r} — the loader reads '...' as a quote; write ’ instead"
                )

        if (folder / "scripts").is_dir() and f"working-directory: skills/{name}/scripts" not in workflow:
            failures.append(
                f"{name}: ships scripts/ but has no CI job in .github/workflows/test.yml"
            )

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
                policy = json.loads((folder / "skill-policy.json").read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(f"{name}: skill-policy.json is not valid JSON ({exc})")
                policy = {}
            tools = policy.get("allowed_tools") or []
            execution = (policy.get("scripts") or {}).get("execution", "approval")
            if (folder / "scripts").is_dir() and execution != "none" and tools and "run_command" not in tools:
                failures.append(
                    f"{name}: ships scripts/ with execution {execution!r} but allowed_tools "
                    f"lacks run_command — the agent cannot run them while the skill is active"
                )
            for tool in tools:
                if tool not in known_tools and not MCP_QUALIFIED_RE.match(str(tool)):
                    failures.append(
                        f"{name}: allowed_tools has {tool!r}, which is not an Aria tool "
                        f"(see scripts/aria_known_tools.json)"
                    )

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

    # A phrase contained in another skill's phrase means every message that
    # fires the second skill also fires the first one.
    for name, phrases in sorted(phrases_by_skill.items()):
        for other, other_phrases in sorted(phrases_by_skill.items()):
            if other == name:
                continue
            for phrase in phrases:
                for other_phrase in other_phrases:
                    if phrase in other_phrase:
                        failures.append(
                            f"{name}: trigger phrase {phrase!r} also fires on "
                            f"{other}'s {other_phrase!r} — make them distinct"
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
                "---\nname: orphan-skill\ndescription: Never registered.\n---\n\n# Orphan\n",
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
