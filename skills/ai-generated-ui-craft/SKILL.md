---
name: ai-generated-ui-craft
description: >-
  The generation-time discipline for an AI producing UI code — not a UI
  category (see `terminal-software-design` for dashboards,
  `conversational-ui-restraint` for chat) but the self-critique process that
  separates a considered design from a templated one. Trigger for "this looks
  AI-generated", "make this feel less generic", "this feels templated", "why
  does every AI-built page look the same", "make this look more deliberate",
  or — proactively — before finalizing any UI generation task, as a
  self-check pass. Trigger regardless of which UI category skill was also
  used; this is orthogonal to both. Do NOT trigger in place of
  `conversational-ui-restraint` for chat-interface structure, or for picking
  an industry direction from scratch (`industry-design-direction`). Portable: self-contained prose,
  no script dependency.
---

# AI-Generated UI Craft

Ask any AI coding assistant to "build a landing page" with no other direction
and the outputs cluster around a small set of tells: warm cream background
with a serif display face and a terracotta accent, or near-black with a lone
neon-green/vermilion pop; a purple-to-blue gradient hero on white; Inter or
Space Grotesk as the "safe" font; emoji used as section markers; everything
centered; `rounded-lg` on every card; an accent bar down the left edge of
rounded cards. None of these are wrong in isolation — the problem is they're
the *default*, reached for the same way regardless of what the page is
actually about, which is what makes the result read as templated rather than
designed.

The fix isn't a better palette to default to instead — any single new default
becomes the next cliché the moment enough people copy it. The fix is a
process: derive every choice from the specific subject in front of you, and
run a self-critique pass that catches genericness before shipping, not after.

## 1. Ground every choice in the specific subject

- Before picking a color, font, or layout, name the one concrete subject,
  its audience, and the page's single job. Distinctive choices come from
  that subject's own vocabulary and materials — a page about a coffee
  roaster and a page about a compiler shouldn't default to the same visual
  language just because both requests said "make it look professional."
- Build with the real content throughout, never placeholder/lorem text —
  a design tuned against fake content will have spacing and hierarchy
  decisions that don't actually hold up once real copy goes in.

## 2. Honor what's already there before inventing something new

- Check for an existing design system first — a tokens file, an agent
  instructions file (`ARIA.md`, `CLAUDE.md`, `AGENTS.md`, …), existing
  component styles in the codebase.
  When one exists, apply it; new choices only fill genuine gaps, they
  never override what's already decided. This single check prevents most
  "looks like a different app pasted in" problems in an existing codebase.
- Only invent a palette/type system from scratch when there's truly
  nothing established yet.

## 3. Choose neutrals and type, don't default to them

- A pure mid-grey background reads as unconsidered; a grey with a slight
  hue bias toward the page's own accent reads as chosen. Pure white or
  near-black are fine grounds when the subject calls for them — the point
  is the neutral was picked deliberately, not inherited because it's what
  comes up first.
- Typography carries the page even when the page isn't about typography.
  Pair a characterful display face used with restraint against a
  complementary body face, plus a utility face for data/captions if
  needed — not the same "safe" pairing reached for on every project
  regardless of subject.

## 4. Design both themes with equal care

- A page that renders in both light and dark should have both themes
  designed, not one theme with the other naively inverted — contrast and
  the accent hue both need to keep working in both directions. If the
  request commits to one visual world on purpose (a single fixed mood),
  that's a legitimate choice — but it should be a choice, not an omission
  because only one theme got attention.

## 5. Spend boldness in one place; keep everything else quiet

- Pick one place to take a real risk — an unusual type pairing, one bold
  color decision, one structural idea — and keep everything surrounding
  it restrained. A page that's loud everywhere has no focal point; a page
  that's quiet everywhere with one considered accent reads as confident.
- If an accent color fights the rest of the palette, shift it toward
  analogous or drop saturation rather than reaching for a second loud
  color to balance it.

## 6. Structure should encode real information, not decorate

- Numbered markers, eyebrows, dividers, and labels should be true about
  the content — a numbered sequence (01/02/03) only belongs on content
  that's actually ordered (a real process, a timeline), not glued onto
  three cards that happen to be side by side. Question every structural
  device: does this tell the reader something true, or is it filling
  space with the *look* of structure?

## 7. The self-critique pass — do this before shipping, every time

Before finalizing, look at the plan (palette, type, layout concept) and ask
of each part: **is this what I'd produce for any similarly-categorized
request, or is it actually specific to this subject?** If a color choice,
font pairing, or layout idea would be equally at home on an unrelated
project, that's the signal to revise it — not because it's bad in the
abstract, but because it isn't actually *derived from anything*. Only after
this check passes does the design plan get built out.

This is the step that's easy to skip under time pressure and is also the
one that most reliably separates "looks AI-generated" from "looks
considered" — everything else in this file is instruction; this step is
the enforcement.

## Checklist

- [ ] Named the specific subject, audience, and page's single job before
      picking any color/font/layout?
- [ ] Checked for an existing design system/tokens file and applied it
      rather than inventing a parallel one?
- [ ] Is the neutral (grey/white/black chosen) deliberately tied to the
      subject, not the first grey that came to mind?
- [ ] Does the type pairing feel specific to this project, not the same
      safe pairing used everywhere?
- [ ] Are both light and dark themes actually designed, not one inverted
      from the other?
- [ ] Is there exactly one place spending real boldness, with everything
      else quiet around it?
- [ ] Would any structural device (numbers, dividers, eyebrows) survive
      the question "does this encode something true about the content"?
- [ ] Ran the self-critique pass: would this same plan show up on an
      unrelated project? If yes, what got revised?
