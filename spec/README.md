# Agent Skill format

A skill is a directory whose entry point is a `SKILL.md` file. Aria reads the
frontmatter of every available skill at all times, but only loads the body when a
task matches the `description`. Keep the frontmatter tight and the body focused.

## Minimum

```
my-skill/
└── SKILL.md
```

```markdown
---
name: my-skill                 # kebab-case, unique, matches the folder name
description: >-                 # the single most important field — it is the
  One or two sentences that     # ONLY thing the agent sees when deciding whether
  say exactly when to trigger   # to load the skill. Name concrete triggers and,
  this skill, in the user's     # if useful, when NOT to trigger.
  own words.
---

# My Skill

The workflow. Write it as instructions to an agent, not prose for a human.
```

## With resources

```
my-skill/
├── SKILL.md
├── references/        # docs the skill points to ("read references/x.md when …")
├── scripts/           # runnable code the skill tells the agent to execute
└── agents/            # per-runtime interface descriptors (display name, prompt)
```

- **`references/`** — longer material the agent loads on demand. The SKILL.md
  body should link to it rather than inlining everything, so the always-loaded
  surface stays small.
- **`scripts/`** — executable helpers. Prefer instructing the agent to *run* a
  script over describing what it would compute. Make scripts self-testing
  (`--demo` or a no-arg smoke path) and dependency-light.
- **`agents/`** — how the skill presents itself in runtimes that need a
  human-facing entry point rather than an auto-fired description. Each file is
  named for its target runtime (`openai.yaml` today). The `description` in
  `SKILL.md` is written for a *classifier* deciding whether to load the skill;
  these fields are written for a *person* picking one off a list, which is why
  they are separate:

  ```yaml
  interface:
    display_name: "Risk Assessment"
    short_description: "Decompose portfolio risk from actual history"
    default_prompt: "Use $risk-assessment to decompose this portfolio's risk."
  ```

  `default_prompt` must reference the skill as `$<name>` so the invocation is
  copy-pasteable. Every skill in this catalog carries one — a skill without an
  interface descriptor is invisible in any runtime that lists skills for a
  human to choose from.

## `skill-policy.json`

Declares what the skill is allowed to reach for. A runtime that enforces
permissions reads this before activating anything; a runtime that doesn't can
ignore it. Unknown keys are ignored, so adding a field is backward-compatible.

```json
{
  "schema_version": "aria.skill-policy.v1",
  "allowed_tools": ["get_market_data", "web_search"],
  "agents": ["fundamental", "technical", "risk"],
  "permissions": ["network", "workspace-write"],
  "scripts": { "execution": "approval", "network": false, "workspace_write": false }
}
```

- **`allowed_tools`** — tool names the skill may call. While a skill is
  active, Aria Code narrows the model's tool schema to its core file tools
  (`read_file`, `analyze_file`, `write_file`, `edit_file`, `multi_edit`,
  `write_spreadsheet`, `export_markdown_pdf`) plus the union of the active
  skills' `allowed_tools`. A name that is not a real tool therefore grants
  nothing, and the tool the author meant is silently unavailable. Use the
  names in [`scripts/aria_known_tools.json`](../scripts/aria_known_tools.json)
  (sourced from aria-code's `apps/cli/local_tool_schemas.py` and tool
  registries) — e.g. `list_files`, not `list_directory`; `backtest_strategy`,
  not `run_backtest`. MCP tools are matched by their short name (the part
  after the last `__`, such as `aria.report.generate_image_local`), or may be
  given fully qualified as `mcp__<server>__<tool>`. A skill that ships
  scripts with `"execution": "approval"` and a non-empty list must include
  `run_command`, or the agent cannot run them. An empty list means no
  narrowing at all.
- **`agents`** — specialist agents the skill orchestrates, by registry name.
  Advisory: the loader never imports an agent registry, so a skill declaring
  agents still loads in runtimes that have none. Declare an agent only if the
  skill actually directs work to it — an aspirational list is worse than an
  empty one, because nothing fails when the agent is absent; the skill just
  quietly does less than its policy claims.
- **`permissions`** — `read-only`, `network`, `workspace-write`, broker levels.
- **`scripts`** — execution posture for anything under `scripts/`. Use
  `"execution": "none"` for reference-only skills that bundle no code.

Reference-only skills still need this file; omit it and the skill loads with
the most restrictive defaults, which is safe but silently wrong if the skill
actually needed a tool.

## Loader limits

Aria Code's loader skips a skill **silently** — no error, no trace — when any
of these fail, so `scripts/validate_catalog.py` checks them in CI:

- `SKILL.md` starts with exactly `---\n` — no byte-order mark, nothing before
  it.
- LF line endings. The loader itself tolerates CRLF, but `skills.lock.json`
  pins a SHA-256 of the raw bytes, so a CRLF checkout fails integrity and the
  skill can no longer activate automatically. `.gitattributes` pins text files
  to LF.
- `SKILL.md` is at most 20,000 characters. Move material into `references/`.
- `name` matches `^[a-z0-9][a-z0-9-]{0,63}$` (and the folder name).
- `description` is non-empty, and there is a non-empty body after the
  frontmatter.

Every skill with a `scripts/` directory also needs a job in
`.github/workflows/test.yml`.

## Description guidance

The `description` is a triggering classifier, not marketing copy. Good
descriptions:

- name the concrete situations that should fire the skill, in the words a user
  would actually use;
- include near-miss phrasings the user might say instead of the technical term;
- state an explicit exclusion when the skill is easy to over-trigger.

### Quoted trigger phrases

Aria Code activates a skill outright when any phrase quoted in its
description — `"…"`, `“…”`, or `'…'` — appears as a substring of the user's
message, wherever in the description the quote sits (an exclusion clause
included). So a quoted phrase is a hard trigger, not an example:

- At least 5 characters (4 if it contains CJK characters), and not a single
  bare English word. `"VaR"` fires on "various", `"done"` on nearly anything,
  `"significant"` on any sentence that uses the word.
- Keep each phrase on one line: a fold inside the quotes becomes a space
  (`"写一个BTC均值 回归策略"`), which no real message contains.
- Do not quote phrases you are only describing or excluding — write them
  unquoted. Write apostrophes as `’`: two ASCII `'` in one description open an
  accidental single-quoted phrase.
- No phrase may be contained in another skill's phrase, or every message that
  fires the other skill fires this one too. Neighbouring skills should each
  carry a "Do NOT trigger for … (use `other-skill`)" clause instead.

Unquoted words still count toward a weaker word-overlap score, so keep
exclusion clauses short and avoid common words there.

## Conventions in this repo

- One concept per skill; split rather than overload.
- Bundled scripts must run from a clean checkout and skip (not fail) when an
  optional dependency is missing.
- Reference docs must stay consistent with the scripts they describe — when the
  code changes, update the reference in the same commit.
