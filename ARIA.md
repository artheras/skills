# Working in this repository

This is a skill catalog, not an application. Every change is either a new skill,
an edit to an existing one, or catalog plumbing. The format itself is documented
in [`spec/README.md`](spec/README.md) — this file covers the *workflow*: what
you must run and update so the catalog stays internally consistent.

## Adding or editing a skill — the four things that must stay in sync

A skill is not "added" until all four are done. All four are enforced by CI
(`scripts/validate_catalog.py` plus the lock check), so skipping one fails the
build rather than silently shipping a broken catalog.

That was not true until the validator existed. The lock check alone cannot see
an unregistered skill, because the lock is *derived from* marketplace.json — a
skill added to disk and never registered produces no stale entry, no failure,
and no installation anywhere. Verified by adding an unregistered probe skill:
the lock check passed, the validator caught it.

1. **The skill folder** — `skills/<name>/SKILL.md`, plus `skill-policy.json`
   and `agents/openai.yaml` (both required), and optionally `references/` and
   `scripts/`. Folder name must match the `name:` in the frontmatter. The
   interface descriptor is not optional: a skill without one is invisible in
   any runtime that lists skills for a human to pick from, which is how 15 of
   16 skills in this catalog were once unreachable that way.
2. **Register it in the marketplace** — add the `./skills/<name>` path to the
   right plugin's `skills` array in
   [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json).
   An unregistered skill exists on disk but is invisible to every runtime that
   installs the catalog as a plugin.
3. **Rebuild the integrity lock** — `python scripts/build_skill_lock.py`.
   CI runs `--check` and fails if the lock is stale. Aria Code's portable skill
   loader verifies against this lock before executing anything, so a stale lock
   is a hard failure, not a warning.
4. **Add a row to the README table** — the catalog table is the human-facing
   index; a skill missing from it is undiscoverable in practice.

If the skill ships runnable scripts, also add a CI job to
[`.github/workflows/test.yml`](.github/workflows/test.yml) following the
existing pattern: a `--demo` smoke run under `-W error::RuntimeWarning`, then
the regression tests.

## Conventions

- **One concept per skill.** Split rather than overload. When two skills could
  both plausibly fire on the same request, say so explicitly in each
  `description` with a "Do NOT trigger for … (use `other-skill`)" clause —
  the description is a triggering classifier, not marketing copy, and
  ambiguity between neighbours is what makes the wrong one load.
- **Keep `SKILL.md` small.** It is always loaded once the skill fires. Longer
  material belongs in `references/`, linked from the body ("read
  `references/x.md` when …"), so the always-loaded surface stays cheap.
- **Prefer running a script over describing what it would compute.** Bundled
  scripts must run from a clean checkout, be dependency-light, and skip (not
  fail) when an optional dependency is missing. Give every script a
  self-testing `--demo` path.
- **Reference docs and scripts change together.** When a script's behaviour
  changes, update the reference doc that describes it in the same commit.
- **`skill-policy.json` is not optional.** Declare `allowed_tools`,
  `permissions`, and the `scripts` execution policy. Reference-only skills
  (no bundled scripts) use `"execution": "none"` with `read-only` permissions.
  See `spec/README.md` for the full field reference, including the optional
  `agents` list. Only declare an agent the skill actually directs work to:
  nothing fails when a declared agent is absent, so an aspirational list makes
  the skill quietly do less than its policy claims.

## Domain guardrail

The catalog spans four plugins: quantitative finance research
(`quant-research-skills`), app engineering and design
(`app-engineering-skills`), operating-rights and revenue-share property
arrangements (`realty-operations-skills`), and third-party logistics
(`logistics-operations-skills`). Skills here produce work product for human
review — they do not make investment recommendations, do not execute trades,
and do not move money. When adding or editing a skill that touches sizing,
execution, payments, or any live-money path, keep the paper-only / read-only
posture explicit in both the skill body and its policy file, and keep the
README's disclaimer accurate with respect to what the catalog can now do.

## Verify before committing

```bash
python scripts/build_skill_lock.py --check   # integrity lock is current
python scripts/validate_catalog.py           # disk / marketplace / policy / descriptor / README agree
```

The validator also enforces Aria Code's loader limits, that every
`allowed_tools` entry is a real Aria tool (`scripts/aria_known_tools.json`),
that quoted trigger phrases are specific enough, and that every skill with a
`scripts/` directory has a CI job — see `spec/README.md` for the rules.

Both are what CI runs. `validate_catalog.py --demo` shows what a failure looks
like against a synthetic broken catalog if you want to see the output shape
without breaking anything.
