#!/usr/bin/env python3
"""Build the integrity lock consumed by Aria Code's portable skill loader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


IGNORED_NAMES = {".DS_Store", ".pytest_cache", "__pycache__"}


def skill_tree_sha256(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in folder.rglob("*") if item.is_file()):
        relative = path.relative_to(folder)
        if any(part in IGNORED_NAMES for part in relative.parts) or path.suffix == ".pyc":
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def build_lock(repository: Path) -> dict:
    marketplace = json.loads(
        (repository / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    catalog_version = str((marketplace.get("metadata") or {}).get("version") or "")
    entries = {}
    for plugin in marketplace.get("plugins") or []:
        plugin_name = str(plugin["name"])
        version = str(plugin.get("version") or catalog_version)
        for relative in plugin.get("skills") or []:
            folder = (repository / relative).resolve()
            skill_name = folder.name
            entries[f"{plugin_name}:{skill_name}"] = {
                "path": folder.relative_to(repository.resolve()).as_posix(),
                "sha256": skill_tree_sha256(folder),
                "version": version,
            }
    return {
        "schema_version": "aria.skills-lock.v1",
        "organization": "artheras",
        "repository": "https://github.com/artheras/skills",
        "catalog_version": catalog_version,
        "skills": dict(sorted(entries.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repository = args.repository.resolve()
    destination = repository / ".claude-plugin" / "skills.lock.json"
    rendered = json.dumps(build_lock(repository), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        try:
            current = destination.read_text(encoding="utf-8")
        except OSError:
            current = ""
        if current != rendered:
            print(f"Skill lock is stale: {destination}")
            return 1
        print(f"Skill lock is current: {destination}")
        return 0
    destination.write_text(rendered, encoding="utf-8")
    print(f"Wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
