# Establishing and enforcing the user's design system

This skill operationalizes the user's own decisions. The method below is how
to get from "I want my app to look coherent" to a validated `design-tokens.json`
and code that stays consistent with it — without imposing any particular look.

## 1. Establish tokens — extract, don't invent

Prefer capturing what the user already has over generating from nothing:

- **They have brand assets / a site / a Figma palette** → extract the hex
  values, type sizes, and radii directly into `design-tokens.json`. The system
  already exists implicitly; you are writing it down.
- **They have existing code** → harvest the colors and radii actually used
  (the linter's normalization logic is the same you'd apply here) and propose
  the recurring ones as tokens, collapsing near-duplicates.
- **They are starting fresh** → this is a conversation, not a script. Ask about
  domain, mood, light/dark needs, and one or two reference products they like.
  The `industry-design-direction` skill is the right tool for exploring
  palette/type options. Once
  they choose, record the choice — the recording is this skill's job.

Emit the file with `python scripts/design_tokens.py --template` as the starting
shape, then fill it with the user's values.

## 2. Validate — objective checks the user can't eyeball reliably

`python scripts/design_tokens.py --validate design-tokens.json` enforces things
that are true or false regardless of taste:

- **WCAG contrast.** Body text below 4.5:1 on its surface is an accessibility
  defect, not a style choice — declare `contrast_pairs` so the validator checks
  every text/surface combination in **both** light and dark. A palette that
  looks refined but fails contrast is failing the user's end users.
- **Monotonic scales.** Radius tiers must be distinct and ordered; spacing steps
  must be consistent multiples of the base. A "scale" with two equal tiers or an
  off-grid step is a scale in name only and quietly produces ragged layouts.

Contrast and scale are non-negotiable down for aesthetics — report failures
plainly. Everything else (which hue, how many tiers) is the user's call.

## 3. Generate — reference tokens, never fresh literals

When building components, every color/radius/spacing value resolves through a
token. The target's syntax is the user's platform; the values are their file.
See `token_schema.md` for the per-target mapping table.

## 4. Enforce — the consistency the generic tools can't give

`python scripts/design_lint.py --tokens design-tokens.json --paths <code>` is
the difference between "a design system" and "a document nobody follows." It
flags any color or radius literal in code that isn't one of the user's tokens —
in SwiftUI, CSS/Tailwind, RN, Flutter, or web markup — so the fifth ad-hoc blue
gets caught at review instead of shipping. This is why a per-user token file
beats a stateless UI generator: the generator has no way to know it drifted;
the linter, holding the user's own file, does.

## 5. Wire the linter into the workflow, not just the review

`design_lint.py` exits non-zero on any error-severity violation, so it belongs
where drift is cheapest to catch — before code lands.

**pre-commit** (`.pre-commit-config.yaml`):

```yaml
- repo: local
  hooks:
    - id: ui-design-system
      name: design tokens
      entry: python path/to/design_lint.py --tokens design-tokens.json --paths
      language: system
      types_or: [swift, css, scss, ts, tsx, javascript, jsx, vue]
      pass_filenames: true
```

**CI** (any runner):

```bash
python design_lint.py --tokens design-tokens.json --paths src/ || exit 1
```

Keep `design-tokens.json` under version control next to the code it governs —
the system and the thing it constrains evolve together.

## Extraction and the linter share one normalization

`--extract` and the linter recognize the same color literal forms (`#rrggbb`,
`Color(red:g:b:)`, `rgb()/rgba()`) and normalize them the same way, so a value
the extractor captures as a token is a value the linter will later accept. The
extractor additionally *clusters* near-duplicates (folding `#2f6bff` and
`#2f6cff` into one token); the linter mirrors that with a small distance
tolerance so the same rounding is accepted at lint time.

## Honest limitation: utility-class frameworks (Tailwind, UnoCSS)

The linter finds off-system **literals**. In a Tailwind project, colors are
usually configured in `tailwind.config` and referenced by semantic class
(`bg-blue-500`), not written as hex in components — so the linter can only
catch *arbitrary values* like `bg-[#ff0000]`, not a class that points at a
palette entry outside the design system. For those stacks, the real check is
that `tailwind.config`'s palette equals `design-tokens.json` (keep them in
sync, ideally generate the config from the tokens) and that arbitrary-value
syntax is disallowed by lint rule. Don't claim full coverage of a Tailwind
codebase from this linter alone.

## Why not just let the model "keep it consistent"?

Because consistency across many sessions and many screens is exactly what a
stateless model is worst at — it re-derives choices each time. Freezing the
decision once (the token file) and checking against it mechanically (the linter)
makes the system a property of the project, not of any one conversation.
