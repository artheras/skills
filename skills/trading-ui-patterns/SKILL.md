---
name: trading-ui-patterns
description: >-
  Build or review a trading/investing-app component against the specific
  conventions of X (timeline post, action bar), TradingView (watchlist row,
  technical rating gauge), or Trading212 (order ticket, holdings row).
  Trigger for "make this look like TradingView", "look like Trading212",
  "watchlist row like TradingView", "order ticket like Trading212", "technical
  rating gauge", "做一个像 TradingView 一样的自选股列表", "参考 X 的帖子卡片样式",
  or when reviewing a finished component against one of these reference
  patterns before shipping it. Also trigger when a watchlist/quote/holdings
  component needs to render more than one market’s data (e.g. both US and
  CN symbols) — this is where the direction-color convention silently
  breaks. Do NOT trigger to invent a generic app aesthetic from a blank
  slate (use `industry-design-direction` for open-ended style exploration) or
  to freeze the user’s own palette/spacing choices into reusable tokens
  (that’s `ui-design-system`) — this skill is specifically about matching one
  of these three products’ own component conventions, not the user’s.
---

# Trading UI Patterns

X, TradingView, and Trading212 each solved a different part of the
"financial app that doesn't feel like a spreadsheet" problem, and the three
solutions are not interchangeable: X's density-and-restraint social feed,
TradingView's tabular-figures terminal chrome, and Trading212's
input-gated simplicity are distinct disciplines with their own failure
modes. Building "in the style of" one of them from memory alone tends to
nail the obvious surface (colors, rounded corners) and miss the structural
details that actually make a component read as that product's — a
watchlist row with no tabular digits, an order ticket whose confirm button
is tappable before the input is valid, a like icon that's already filled
red before anyone has tapped it.

## The one failure mode a naive rebuild won't catch on its own

Direction color (red/green for up/down) is not a fixed constant — it is a
function of which market's convention the data represents. US/UK/HK/most of
the world uses green=up/red=down; mainland China and Taiwan use the
opposite (red is auspicious, associated with rising prices). A watchlist or
holdings row built and screenshot-checked against US test data, then pointed
at a CN symbol feed without re-deriving the color mapping, renders every
single quote backwards — and nothing crashes, nothing looks obviously wrong
in a screenshot taken by someone who doesn't already know the correct CN
convention. This is the same shape of bug as a sign-convention flip in a
quant computation (see the `gamma-exposure` skill), just expressed as a
color instead of a number. `scripts/pattern_audit.py --demo` reproduces it
on a synthetic manifest.

## Workflow

1. **Identify the pattern.** `python scripts/pattern_audit.py --list` prints
   every known pattern id, its source product, and a one-line description.
   If the component doesn't match any of these closely, read the relevant
   `references/<product>_patterns.md` anyway for adjacent conventions, but
   don't force-fit an audit against a pattern it isn't actually implementing.
2. **Read the pattern's reference doc before building** —
   `references/x_patterns.md`, `references/tradingview_patterns.md`, or
   `references/trading212_patterns.md`. Each covers the structural elements,
   the specific "what breaks the pattern's identity" anti-patterns, and any
   market-dependent field for that pattern. This is where the actual design
   knowledge lives — the audit script only checks structure, not the prose
   conventions (tabular digits, relative timestamps, icon fill-on-activation).
3. **Build the component** against the target's real syntax (SwiftUI, CSS/
   Tailwind, React Native, Flutter — whatever the project uses), following
   the reference doc's structural and stylistic conventions. If the user
   already has a `design-tokens.json` (see `ui-design-system`), colors/radii/
   spacing should still come from their tokens — this skill governs
   structure and convention, not where the literal values come from.
4. **Write a component manifest** describing what you built — see
   `references/methodology.md` for the exact shape. This is a deliberately
   small JSON (`pattern`, optional `market`, and a `fields` dict of what's
   actually present), not a screenshot or the source code itself.
5. **Audit it**: `python scripts/pattern_audit.py --manifest component.json`.
   FAIL findings (`missing_required_field`, `forbidden_condition_present`,
   `market_convention_mismatch`, or a `rule_violation` at fail severity) mean
   the component doesn't yet read as the claimed pattern or is wrong for its
   declared market — fix before shipping. WARN findings
   (`missing_recommended_field`, warn-severity `rule_violation`) are
   judgment calls: the component is structurally sound but thinner than the
   reference; note them rather than silently drop them.
6. **Building for more than one market?** Always set `market` in the
   manifest and re-run the audit per market the component actually serves —
   a watchlist row correct for `US` is not automatically correct for `CN`,
   and the audit will not catch a market-aware field it wasn't told the
   target market for.
7. `python scripts/pattern_audit.py --demo` to see the market-convention bug
   and its fix side by side with no files needed.

## Guardrails

- Never assume a market's direction-color convention without checking —
  default to asking or reading `references/tradingview_patterns.md`'s
  convention table rather than guessing from another market's build.
- A PASS/WARN verdict describes structural completeness against the
  checklist, not visual quality — the audit cannot see whether the spacing
  actually feels right, only whether the required pieces exist. Taste
  judgment still belongs to the conversation, not the script.
- Don't force a component into a pattern id it doesn't really implement just
  to get a report — an honest "this doesn't match any cataloged pattern
  closely" is more useful than a misleading audit against the wrong checklist.
- Adding a new pattern is a `references/patterns.json` edit plus a
  `references/<product>_patterns.md` prose addition — never hardcode a new
  pattern's logic directly into `pattern_audit.py`; see
  `references/methodology.md`.

## Bundled resources

- `scripts/pattern_audit.py` — `audit_manifest()` runs the deterministic
  checklist (required/recommended/forbidden fields, numeric/equality rules,
  market-aware convention checks) against `references/patterns.json`.
  `--list` prints the catalog, `--manifest FILE` audits a component,
  `--json FILE` writes a machine-readable report, `--demo` reproduces the
  market-convention bug and its fix with no files needed.
- `references/patterns.json` — the pattern catalog itself: required/
  recommended/forbidden fields, rules, and market-aware fields per pattern.
  Edit this to extend the catalog; see `references/methodology.md`.
- `references/x_patterns.md` — X's timeline post and action bar conventions.
- `references/tradingview_patterns.md` — TradingView's watchlist row and
  technical rating gauge conventions, including the full direction-color
  market table.
- `references/trading212_patterns.md` — Trading212's order ticket and
  holdings row conventions.
- `references/methodology.md` — the manifest shape, the division of labor
  between taste and machine checks, and how to extend the pattern catalog.
