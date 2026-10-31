---
name: minimal-editorial-exports
description: >-
  An alternate visual style for aria-code’s own generated exports — report
  covers, PPTX title slides, single-chart share images, Canva one-pagers —
  built on heavy negative space, one accent color, and restrained
  serif/monospace type, instead of the default dense institutional/dashboard
  look. Trigger for "极简封面", "极简风格的报告封面", "杂志风封面",
  "editorial cover", "editorial-style export", "zine-style cover", "make the
  cover less corporate", "make the cover page quieter", "one number, lots of
  white space", or when the user wants a report/deck/chart export that reads
  as considered rather than templated-dashboard. Do NOT trigger for the
  default financial report body (tables, indicators, full analysis) — this
  governs cover pages, title slides, and single-focal-point exports only,
  never dense data views (use `terminal-software-design` or the existing
  institutional/bloomberg themes for those). Do NOT trigger for a standalone
  poster from a theme or story (use `minimal-editorial-poster`). Do NOT
  trigger to invent a generic aesthetic from nothing — use
  `industry-design-direction` for open-ended exploration instead.
---

# Minimal Editorial Exports

Financial report tooling defaults to density — dark tables, corporate blue,
every indicator visible at once — because that's what the *body* of a report
needs. But aria-code also produces things that aren't report bodies: a cover
page, a PPTX title slide, a single chart meant to stand alone, a Canva
one-pager. Applying the dense-dashboard default to those is a mismatch: a
cover page crammed with the same density as the analysis behind it reads as
unfinished, not thorough. The fix is a second, deliberately restrained style
for exactly these single-focal-point surfaces — heavy negative space, one
accent color, one number or one chart doing the work, quiet typography
carrying the rest. Silence read as confidence in print design long before
software existed; the same logic applies here.

## When this matters

- A report's cover page or first slide, before the dense analysis begins
- A PPTX title slide (`aria.report.pptx` / `report_exporters.py`)
- A single chart meant to be shared standalone, not embedded in a full report
- A Canva brand-template autofill for a one-pager or social export
- Never the report *body* — tables, multi-indicator panels, and the
  institutional/bloomberg themes stay dense on purpose; this style is for the
  one surface per document that's allowed to be quiet

## Design rules

1. **70%+ quiet space.** The cover/title surface should be mostly negative
   space around one focal point — one number (e.g. the headline return), one
   chart, or one signal — not a summary of everything the document contains.
2. **One accent color, tied to real meaning.** If there's a directional
   signal, the accent is that signal's real color (gain/loss, buy/sell) —
   never a decorative color chosen for mood. If there's no signal, pick one
   restrained anchor color and don't reach for a second.
3. **Restrained type, not the safe default.** Serif or monospace over the
   generic sans-serif dashboard default; one size doing the heavy lifting
   (the headline number or title), everything else quiet caption-weight.
4. **Texture only where the format supports it.** An HTML/PDF cover
   (`report_generator.py`'s `export_pdf` path) can carry a subtle
   paper-grain or noise background; PPTX/DOCX covers (`report_exporters.py`)
   can't render texture the same way — for those, let space and type do the
   work instead of trying to fake grain.
5. **No borrowed dashboard chrome on the cover.** No sidebar, no nav, no
   multi-panel grid — a cover that reuses the report body's chrome isn't
   restrained, it's just a smaller dashboard.

## Applying this in aria-code

- **`report_generator.py`** — `generate_price_chart`'s `mpf.make_marketcolors(...)`
  call sets the chart palette; for a standalone/cover chart, drop it to a
  single accent + neutral rather than the full up/down + volume palette used
  in the report body.
- **`pdf_report.py`** — `THEMES` (`institutional`, `bloomberg`) are both
  dense-body themes; this style is for the *cover page* those themes render
  before the body starts, not a competing third dense theme.
- **`report_exporters.py`** — `markdown_to_pptx`'s title slide (the first
  slide, before per-heading slides start) is the one slide this style
  governs; keep it to one line of restrained type and real negative space,
  not a bullet list. Same for `markdown_to_docx`'s cover heading.
- **`canva_client.py`** — when building the brand template this style
  targets, keep the template itself minimal (one text field, one optional
  image/chart field); `autofill_design`'s `data` argument should carry one
  headline value, not a dense field set.

## Variation axes — don't let every export look identical

Run this style enough times (one cover per symbol, one title slide per
report) and a single fixed recipe becomes its own template — the exact
genericness problem `ai-generated-ui-craft` warns about, just at the style
level instead of the whole-page level. The fix isn't random variation
(a randomly-placed layout on a financial document reads as arbitrary, not
considered) — it's varying along a few independent axes, each driven by
something real about *this* export, not a dice roll:

- **Focal-point position** — centered / lower-third / upper-block. Derive
  from something real when possible (e.g. a strong directional signal
  implies weight toward one side) rather than defaulting to centered every
  time purely out of habit.
- **Focal-point type** — one number (headline return/price), one chart
  (`aria.report.chart`'s output), or one short line of text — pick whichever
  actually carries this specific report's story; don't reach for "always the
  chart" or "always the number" regardless of what the report is about.
- **Type pairing** — serif-only, monospace-only, or a serif headline +
  monospace caption pair. Rotate deliberately across a batch (e.g. a
  multi-symbol daily digest) rather than letting every export in the same
  run pick the same pairing by default.
- **Quiet ratio** — 70% vs 85%+ negative space is itself a choice, not just
  a floor; a headline-only cover can afford more silence than one carrying a
  chart.

None of these axes touch the accent-color rule above — the accent stays
tied to real signal meaning regardless of which layout/type/quiet-ratio
combination gets picked.

## Automated Quality Gate

`scripts/exports_gate.py` turns the checklist below into code, the same
pattern `minimal-editorial-poster`'s `poster_gate.py` uses (these two skills
are siblings — keep the two gates' shape aligned if one changes). Build a
spec with `surface`, `export_format`, `quiet_pct`, `focal_point`,
`focal_point_type`, `accent_color` (`{name, hex, source}`), `typography`,
`texture`, `chrome_notes`, and — when part of a batch —
`is_batch`/`variation_axis`/`variation_reason`, then:

```bash
python scripts/exports_gate.py --spec spec.json
python scripts/exports_gate.py --demo
```

`--demo` compiles a dense cover wearing a "minimal" label (25% quiet space,
borrowed sidebar/nav chrome, texture on a PPTX slide that can't render it,
Inter/system-ui type) next to the corrected minimal-editorial compile for
the same report — the first FAILs with named codes
(`insufficient_quiet_space`, `borrowed_dashboard_chrome`,
`texture_unsupported_by_format`, …), the second PASSes.

## Checklist

- [ ] Is at least 70% of the cover/title surface genuinely quiet, not just
      slightly less dense than the body?
- [ ] Is the one accent color tied to something real (a signal), or at least
      chosen once and not fought by a second color?
- [ ] Is the type restrained and specific, not the default dashboard sans?
- [ ] Did texture only get used where the export format can actually render
      it (HTML/PDF), not faked on PPTX/DOCX?
- [ ] Does the cover avoid reusing the report body's chrome (sidebar, nav,
      multi-panel grid)?
- [ ] Is this being applied to a cover/title/single-focal surface, not the
      dense report body itself?
- [ ] If generating more than one export in the same run/batch, does the
      focal-point position, focal-point type, or type pairing actually vary
      across them — driven by something real, not left on autopilot?
