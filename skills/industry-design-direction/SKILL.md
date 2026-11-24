---
name: industry-design-direction
description: >-
  Pick a concrete visual direction for a website or app in a specific industry —
  which aesthetic, which palette, which font pairing, which page structure —
  from a library of 95 industry profiles, 57 defined styles, 96 palettes, 57
  font pairings, and 30 landing structures. Trigger for "design a landing page
  for a dental clinic", "帮我设计一个餐厅网站", "what should a fintech app look
  like", "给这个 SaaS 产品定一套配色和字体", "我要做一个电商网站，用什么风格",
  or whenever someone needs a starting direction for a product whose industry
  is known but whose look is not.
  Do NOT trigger once a direction already exists and the job is enforcing it
  across screens (use `ui-design-system` — that skill operationalizes a chosen
  aesthetic into tokens; this one chooses it). Do NOT trigger for dense
  dashboards/terminals (`terminal-software-design`), chat interfaces
  (`conversational-ui-restraint`), or trading-app components
  (`trading-ui-patterns`) — those are category skills with far more depth for
  their category than the one-line profile here. Every reference file is
  self-contained prose usable in any assistant; the bundled
  `scripts/verify_contrast.py` data-integrity gate needs Python.
---

# Industry design direction

Most generated UI looks templated because the aesthetic was never actually
chosen — it defaulted. Purple-blue gradient, glassmorphic cards, Inter
everywhere, hero-features-CTA. That default is applied identically to a
dental clinic, a metal fabricator, and an NFT marketplace, and it is wrong for
all three in different ways.

This skill exists to make the choice explicit and industry-grounded, before
any component is written. It is the *exploration* step. Once a direction is
picked, `ui-design-system` turns it into enforceable tokens.

## The five decisions, in this order

Order matters — each one constrains the next, and taking them out of order is
how you end up retrofitting a palette onto a layout that fights it.

1. **Industry profile** → `references/industry_profiles.md`
   Find the row matching the product. Match on the profile name *or* its
   keywords: users describe products in their own words ("clinic booking
   site"), not in the library's labels ("Healthcare App"). This gives you the
   primary style, viable alternates, the page structure, and — the part most
   worth reading — the constraint that industry most often gets wrong.

2. **What that style actually is** → `references/style_library.md`
   The profile *names* a style; this defines it — colors, effects, theme
   support, performance, the CSS that produces it, and a done-checklist.
   Read the **"Do NOT use for"** line before the "Best for" line: a style
   applied to the case it explicitly fails at is worse than a plain default.
   Skipping this step is how a named style silently collapses back into
   whatever the model already assumed it meant.

3. **Palette** → `references/color_palettes.md`
   Same product-type key as the profile. Six roles: Primary, Secondary, CTA,
   Background, Text, Border. Take all six; picking only a primary and
   improvising the rest is how the neutral tones drift grey and the whole page
   flattens.

4. **Type pairing** → `references/typography_pairings.md`
   Filter by the *Best for* line, not by what looks nice in isolation. A
   heading/body split is what stops a page reading as one undifferentiated
   block — a single family everywhere is the single most reliable tell of
   generated UI.

5. **Page structure** → `references/landing_patterns.md`
   Use the structure named in the industry profile. Each entry gives section
   order, where the primary CTA sits, a color strategy for that structure, and
   what actually converts for it.

## What the library will not do for you

- **It has no opinion about your specific brand.** If the user already has
  brand colors, their colors win — use the library for the *roles* the palette
  is missing (border, background, CTA-vs-primary separation), not to overrule
  a decision they already made.
- **Two industries often both fit.** A therapy-practice booking site is
  plausibly Healthcare App, Mental Health App, or Hyperlocal Services. Read
  all the candidates and say which you picked and why — the "most-missed
  constraint" line is usually the tiebreaker.
- **The profile is one line per industry, not a design system.** For dense
  dashboards, chat UIs, or trading components, the category skills named in
  the description have real depth; this gives you a direction, they give you
  the component-level craft.

## Accessibility: what is verified and what is not

Every palette's **body-text-on-background** ratio was computed with the WCAG
2.x relative-luminance formula and clears AA (4.5:1). That is the only pair
verified.

Any other pairing is yours to check — most importantly **label text on the
CTA color**, which is the pair most likely to fail in practice and the one no
palette table can pre-verify, because it depends on whether you put white or
dark text on that button. Check it before shipping, not after.

## Workflow

1. Identify the industry from what the user described. If genuinely ambiguous
   between two profiles, read both and pick with a stated reason — do not
   silently average them into something generic.
2. Read the five references in the order above, taking the specific values.
3. Present the direction as a short brief: style, six-role palette with hex
   values, heading/body fonts with their `@import`, and the section order.
   State the industry's most-missed constraint explicitly — that line is the
   reason the direction is what it is.
4. Run the quality gate below before handing it over.
5. If the user then wants this enforced across many screens, hand off to
   `ui-design-system` to capture it as tokens. If they want it critiqued for
   genericness after building, hand off to `ai-generated-ui-craft`.

## Automated Data-Integrity Gate

`references/color_palettes.md` opens with a factual claim: every printed
contrast ratio was computed, not guessed, and all 96 palettes clear AA
(4.5:1) for body text. Nothing enforced that claim stays true after the file
gets hand-edited — a nudged hex value can silently invalidate a printed
number that still reads as verified. `scripts/verify_contrast.py`
re-derives every palette's ratio from its Background/Text hex pair via the
WCAG relative-luminance formula and diffs it against the file's own printed
value:

```bash
python scripts/verify_contrast.py          # audits references/color_palettes.md
python scripts/verify_contrast.py --demo   # no data needed
```

Run this after any edit to `color_palettes.md`, and periodically otherwise —
it is the only thing standing between "computed, not claimed" staying true
and quietly becoming false. `--demo` shows a clean palette passing next to
the same palette with one hand-nudged hex, which fails with `ratio_mismatch`
and `fails_aa_body_text`. This is a data-integrity gate, not a design-
judgment one — it has nothing to say about which palette to *pick*, only
about whether the numbers next to it are still true.

## Quality gate

- [ ] Did the industry profile actually change the output, or would this same
      direction have been produced for any product? If the latter, you
      defaulted — go back to step 1.
- [ ] All six palette roles specified, not just a primary?
- [ ] Heading and body are *different* families, with a stated reason for the
      pairing beyond "it looks modern"?
- [ ] Style looked up in `style_library.md`, and its "do NOT use for" line
      checked against this product — not just the style's name repeated?
- [ ] Section order taken from a named structure, not improvised?
- [ ] The industry's most-missed constraint stated out loud, and visibly
      reflected in the direction rather than just quoted?
- [ ] CTA-label contrast checked (the one the library cannot pre-verify)?
- [ ] If the user supplied brand colors, do they still win?

## References

- `references/industry_profiles.md` — 95 industry profiles: style, alternates,
  page structure, dashboard style, palette direction, most-missed constraint
- `references/style_library.md` — 57 styles defined: colors, effects, theme and
  performance support, CSS, token starting points, done-checklists, and an
  explicit "do not use for" per style
- `references/color_palettes.md` — 96 six-role palettes with hex values and
  computed text/background contrast ratios
- `references/typography_pairings.md` — 57 Google-Fonts pairings with mood,
  best-for, `@import`, and Tailwind config
- `references/landing_patterns.md` — 30 page structures: section order, CTA
  placement, color strategy, effects, conversion notes
