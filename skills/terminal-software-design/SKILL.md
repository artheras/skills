---
name: terminal-software-design
description: >-
  Build or review UI for a terminal, IDE, trading/data dashboard, admin/ops
  tool, or any dense data-driven desktop/web app — as opposed to a marketing
  site or landing page. Trigger for "review my sidebar", "why does this look
  unfinished", "dashboard feels too sparse", "dashboard feels too dense",
  "Electron window has a weird line at the edge", "make this table easier to
  scan", "这个侧边栏要怎么改", "为什么这个终端界面看起来不对", or when reviewing
  a finished screen/component in one of these product categories before
  shipping it. Portable: every reference file here is self-contained prose
  with no script dependency — it works pasted as instructions into any
  assistant, not only inside this harness. Do NOT trigger to invent a generic
  app aesthetic from a blank slate (use `industry-design-direction`), to match
  one specific reference product’s own conventions like TradingView/X/Trading212
  (use `trading-ui-patterns`), or to freeze the user’s own palette/spacing into
  reusable tokens (use `ui-design-system`) — this skill is the
  density/composition/native-chrome discipline that applies regardless of
  which of those you’re also doing.
---

# Terminal & Software UI Design

Software that is **operated**, not read, follows a different discipline than
marketing/landing-page design, where whitespace and a single hero read as
quality. In a tool people use for hours a day, whitespace that pushes real
content off-screen reads as *unfinished*, not elegant. A naive review pass
tends to catch the obvious stuff (contrast, spacing) and miss the failure
modes specific to this category: a sidebar that fills 100% of a narrowed
window while the actual content disappears, a popover that blends into its
own background, a native Electron window bleeding the wrong theme color at
its edges before the page even paints.

## Workflow

1. **Read `references/density_and_semantics.md` first** — the core
   inversion (density is correct here, not a compromise), semantic-vs-brand
   color, tabular numeric data, and keyboard-first interaction. This is the
   base judgment everything else builds on.
2. **Read `references/component_patterns.md`** for the specific failure
   modes in sidebars, popovers/menus, segmented toggles, and sibling
   surfaces (two panels that are supposed to read as the same UI layer but
   use different tokens).
3. **Building or reviewing an Electron app?** Read
   `references/electron_chrome_pitfalls.md` — native window background
   bleeding at theme boundaries, traffic-light centering, why the
   in-app theme toggle doesn't automatically reach native chrome. These
   bugs don't show up in web-only design guides.
4. **`references/worked_examples.md`** has four real before/after bugs from
   a production trading terminal, cross-referenced from the sections above
   — read the relevant one when you want a concrete example instead of the
   abstract rule.
5. When reviewing a screenshot or a live app, walk it against the checklist
   below before calling it done.

## Checklist

- [ ] Does any panel have visible dead space with no plan to fill it, or is
      the empty state sized to its actual container?
- [ ] Is semantic color (state) kept separate from the brand accent color?
- [ ] Do numeric columns use tabular/monospace alignment and fixed decimal
      precision?
- [ ] Does every primary action have a keyboard path, and does Esc close
      every modal/popover?
- [ ] Do all "same layer" sibling surfaces use the literal same background
      token, not visually-similar-but-different tokens?
- [ ] Does every floating panel have a real shadow/border distinct from its
      background, and does it fully clear the element that triggered it?
- [ ] (Electron only) Does the native window background match the *current*
      resolved theme, synced on every theme change — not a value hardcoded
      once at window creation?

## Bundled resources

- `references/density_and_semantics.md` — density, semantic color, tabular
  data, keyboard-first. Read this first.
- `references/component_patterns.md` — sidebar, popover, segmented toggle,
  sibling-surface, and working-tool empty-state patterns.
- `references/electron_chrome_pitfalls.md` — native window background sync,
  traffic-light positioning, theme-sync gotchas.
- `references/worked_examples.md` — four real before/after bugs, cross-
  referenced from the sections above.
