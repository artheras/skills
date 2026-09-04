---
name: ui-design-system
description: >-
  Help the user build and enforce *their own* design system — capture their
  brand/aesthetic decisions into a portable design-tokens.json, then keep
  every UI they generate consistent with it. Trigger for "帮我建立设计系统",
  "把我的品牌色定成规范", "make my UI consistent", "set up design tokens",
  "check this screen matches my design system", "为我的 app 定一套配色和圆角规范",
  "review my components against my tokens", or whenever the user is building
  UI and wants coherence across screens rather than one-off styling. Do NOT
  trigger to invent an aesthetic from a blank slate with no user input (ask
  them, or use ui-ux-pro-max for exploration first) — this skill operationalizes
  the user's OWN choices, it does not impose a house style. Works across
  targets (CSS/Tailwind, SwiftUI, React Native, Flutter) because tokens are
  platform-neutral.
---

# UI Design System

This skill does not have a look of its own. Its job is to take **the user's**
design decisions — their palette, type scale, radius tiers, spacing rhythm —
and (1) freeze them into one portable `design-tokens.json` the user owns, then
(2) hold every UI they generate to that file. A generic UI helper has no
memory: it picks a slightly different blue and a slightly different radius each
session, and the product ends up looking assembled by five people. The
durable value here is **the user's own consistency**, enforced deterministically.

## Division of labor — what is a taste call vs a machine check

- **Taste calls** (which blue, serif vs sans, playful vs austere) belong to
  the user, reached through conversation — draw on `ui-ux-pro-max` for options
  if they want to explore. This skill never overrides those with a preferred
  style.
- **Machine checks** (is text readable on canvas, is the radius scale
  monotonic, does this component use a color that isn't in the system) are
  objective. Those are what the bundled scripts enforce — no opinion, just the
  user's own tokens applied consistently.

## Workflow

1. **Establish the product ontology before styling.** Write one sentence for
   each of: the product's enduring identity, its current core capability, its
   first proven application domain, and its longer-term direction. Do not let
   an application domain silently become the brand itself. Then inventory
   which claims are shipped, demonstrated, measured, or directional. Use
   `references/product_ontology.md` for the brief and evidence rules.
2. **Establish the tokens.** If the user has existing code, harvest what it
   already uses — `python scripts/design_tokens.py --extract src/` scans the
   codebase, clusters near-duplicate colors, and prints a tokens *draft* to
   rename and prune (the system already exists implicitly; you are writing it
   down). If starting fresh, converse to pin down choices (lean on
   `ui-ux-pro-max` for exploration), then record them — `python
   scripts/design_tokens.py --template` prints the annotated skeleton to fill.
   Either way the result is a `design-tokens.json` in the user's project.
   Schema lives in `references/token_schema.md`.
3. **Validate the tokens are sound** (objective, not aesthetic):
   `python scripts/design_tokens.py --validate design-tokens.json`. Checks
   schema completeness, WCAG contrast of each text color against its surface
   (< 4.5:1 body text is flagged), radius/spacing scales are monotonic, and
   spacing steps are consistent multiples of the base. Report failures; a
   pretty palette that fails contrast is not the user's friend.
4. **Generate UI against the tokens.** When building components (any target),
   every color/radius/space references a token, never a fresh literal. The
   target's syntax is the user's choice; the values come from their file.
5. **Enforce consistency.** `python scripts/design_lint.py --tokens
   design-tokens.json --paths <files/dirs>` scans generated code for
   color/radius literals that are NOT in the user's token set, and (per the
   user's declared convention) emoji-as-icon. Verdict first: violations
   file:line grouped by rule, then the fix routes to the token that should
   have been used.
6. **Iterate on the system, not around it.** If a screen genuinely needs a
   value the tokens don't have, that is a change to `design-tokens.json`
   (a considered addition the user makes), re-validated — not a one-off
   literal smuggled into one component.

## Guardrails

- The token file is the user's, and its conventions govern. `emoji_icons`
  defaults to `forbid` (emoji render inconsistently across platforms, can't be
  tinted, carry no a11y label) but the user can set `allow` in their own file —
  the skill does not hardcode this preference.
- Never substitute a value the user didn't choose. If a token is missing, ask
  or flag it — do not quietly pick a color "that looks close."
- Never turn a launch domain into the product identity without the user's
  explicit decision. Navigation, hero copy, proof, and imagery must preserve
  the hierarchy between enduring identity, core capability, and application
  domains.
- Do not fabricate metrics, customer logos, testimonials, uptime, latency, or
  maturity. Label roadmap capabilities as direction; label prototypes as
  demonstrations. A visually persuasive claim still needs a real evidence
  state.
- Open-source references are inputs, not a visual identity. Verify the license
  at the path used, record what is being adopted, and copy neither another
  product's brand expression nor proprietary example applications. See
  `references/product_ontology.md`.
- Contrast and scale checks are objective and not negotiable down for
  aesthetics: failing body-text contrast is an accessibility defect, reported
  as such regardless of how the palette looks.
- This skill enforces a system; it does not author one from nothing. With no
  user input to operationalize, the deliverable is the questions to ask, not a
  fabricated house style.

## Bundled resources

- `scripts/design_tokens.py` — scaffolds (`--template`), extracts a draft from
  existing code (`--extract PATH...`), and validates (`--validate`) the user's
  `design-tokens.json`: schema, WCAG contrast, monotonic scales. `--demo` for a
  self-contained smoke test.
- `scripts/design_lint.py` — enforces generated code against the user's tokens
  (`--tokens FILE --paths ...`) across every dimension the file declares:
  off-system color literals (error; rounding tolerance + nearest-token
  suggestion) — recognized as `#rrggbb`, `Color(red:g:b:)`, `rgb()/rgba()`, and
  `Color(hex:"…")` (the `#` is often omitted); chromatic system colors like
  `Color.green`/`.red` (warn) since they bypass the palette by definition
  (neutral white/black/gray are left alone); and off-system radius / font-size /
  spacing literals (warn; each linted only if that block exists in the tokens,
  each with a nearest-token hint). Emoji rule per the file's own convention.
  `--demo` for a self-contained smoke test. Exits non-zero on any error-severity
  violation, so it drops into a pre-commit hook or CI step — see
  `references/methodology.md`.
- `references/token_schema.md` — the platform-neutral `design-tokens.json`
  schema, with field meanings and target-mapping notes.
- `references/methodology.md` — how to establish tokens from user input
  (extract vs. converse), contrast/scale rationale, and how tokens map to each
  target's syntax.
- `references/product_ontology.md` — separates enduring identity, capability,
  application domains, and roadmap; defines claim evidence states and a
  license-aware method for learning from open-source design systems.
