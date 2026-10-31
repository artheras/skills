---
name: conversational-ui-restraint
description: >-
  Build or review a chat/copilot/assistant interface — message list, composer,
  streaming responses, conversation sidebar, canvas/side-panel for structured
  output. Trigger for "make this chat UI look like ChatGPT", "chat UI like
  Claude", "为什么我的对话界面看起来很乱", "streaming response feels janky",
  "conversation sidebar needs work", "chat UI feels cluttered", or when
  reviewing a chat/assistant screen before shipping it. This is a DIFFERENT
  problem than dense dashboards — a chat UI’s job is to get out of the way of
  the content, not to show more data per screen (use
  `terminal-software-design` for tables/dashboards/data grids, not this). Do
  NOT trigger for a cross-category templated-look critique of a non-chat
  page (use `ai-generated-ui-craft`), to invent a generic app
  aesthetic from a blank slate (use `industry-design-direction`), or for
  landing pages. Portable: self-contained prose, no script dependency — works
  pasted into any assistant.
---

# Conversational UI Restraint

The best chat/assistant interfaces (ChatGPT, Claude.ai, Codex) don't look good
because of a secret tool — they look good because of a small set of disciplines
applied consistently, all pointing the same direction: **the interface should
disappear and the content should be the only thing anyone remembers.** This is
the opposite instinct from `terminal-software-design`, where density is
correct — here, restraint is correct, because the "data" is prose, and prose
needs room to be read, not scanned.

A naive attempt at "make it look like ChatGPT" tends to copy the surface (a
gray sidebar, rounded message bubbles) and miss the actual discipline
underneath: near-monochrome color reserved for signal, content-first visual
hierarchy, one consistent icon language, motion that serves comprehension
rather than decorates it.

## 1. Color: monochrome first, color is a signal not a decoration

- Default to a near-monochrome palette (grays/whites/near-blacks) for the
  interface chrome itself. Reserve actual color for things that mean
  something: a link, a syntax-highlighted token, a status indicator, the
  one brand accent used sparingly (a send button, a selected state).
- If everything has a little color — every icon tinted, every card with an
  accent border — nothing stands out, and the page reads as decorated
  rather than considered. The restraint itself is the signal of quality.
- Dark and light mode both need this discipline independently — a dark
  theme with the same near-monochrome restraint reads calm; a dark theme
  where every element got a random accent color to "pop" reads busy.

## 2. Content is the star; chrome recedes

- Message content gets the most visual weight: best contrast, most
  generous line-height, comfortable measure (~60-75 characters per line
  for prose). UI chrome (timestamps, avatars, action icons) should be
  quieter — smaller, lower contrast, revealed on hover rather than always
  fighting for attention.
- Don't let structural UI (borders around every message, heavy card
  shadows per bubble) compete with the text. A hairline separator or
  whitespace alone is usually enough to distinguish turns — test removing
  the border before adding one.
- Code blocks, tables, and structured data inside a conversation should
  look distinctly different from prose (monospace, a subtle background
  tint) so the eye can tell at a glance which register it's reading in.

## 3. One icon language, used sparingly

- Pick one icon set (consistent stroke width, consistent corner radius)
  and never mix in a second family — a rounded-corner icon next to a
  sharp-corner one from a different set is one of the fastest tells that
  a UI wasn't considered as a whole.
- Most actions in a chat UI don't need an icon at all — text labels are
  often clearer than an icon for anything beyond the handful of universal
  ones (send, attach, copy, more). Icon-only buttons need a tooltip or
  they're a guessing game.

## 4. Motion serves comprehension, not decoration

- Streaming text should feel like the model is *thinking and writing*, not
  like text is being typewriter-animated for effect — token-by-token
  reveal with no extra easing/bounce on top of it.
- Loading states (thinking, searching, running a tool) should show
  *what's actually happening* when possible ("Searching the web…",
  "Reading 3 files…") rather than a generic spinner — this is honesty as
  much as it is craft; don't imply progress on work that isn't happening.
- Avoid animating things that don't need it: a new message appearing
  doesn't need a slide-and-fade entrance, it needs to just be there. Motion
  budget is scarce — spend it on the one or two moments that actually
  benefit (a response starting to stream, a tool call resolving), not
  scattered across every state change.

## 5. Progressive disclosure: keep the conversation clean

- When output has real structure (a document, a code diff, a generated
  image, a chart), don't force it into the linear message stream — surface
  it in a side panel/canvas that opens next to the conversation, so the
  chat itself stays a clean record of the exchange rather than a scroll of
  giant embedded artifacts.
- The side panel itself should follow `terminal-software-design`'s density
  rules once it's showing structured content (a document, a diff, a
  table) — the conversational restraint above applies to the chat pane,
  not to every panel in the app.
- Conversation sidebar (history list): compact rows, no per-item card
  chrome — a hover state and the title/date is usually enough. This is a
  list to scan and pick from, not content to read, so it can be denser
  than the message pane itself.

## 6. Empty and onboarding states

- A first-run empty state should suggest the next concrete action in the
  product's own vocabulary (a few example prompts specific to what the
  tool actually does), not a generic "How can I help you today?" with no
  grounding in the product.
- Don't over-decorate the empty state to compensate for having nothing to
  show yet — a centered greeting plus a few real example actions is
  usually enough; a large illustration or animation here reads as filling
  space rather than being helpful.

## 7. Coding-agent-specific conventions (Codex-style)

If the conversation involves code/file changes rather than pure prose:

- Diffs use the standard +/- color convention (additions/removals), never
  a novel scheme — this is the one place where inventing your own visual
  language actively hurts comprehension.
- File paths render as breadcrumbs or truncated-with-tooltip, never
  wrapped mid-path.
- Long tool output (command results, file listings) collapses by default
  with an explicit expand — showing everything inline turns the
  conversation into a wall of logs.
- Task/step status (running, done, failed) needs a consistent glyph +
  color pairing used identically everywhere it appears, not styled
  per-context.

## Checklist

- [ ] Is color reserved for signal (links, status, one accent), not
      scattered as decoration across icons/cards?
- [ ] Does message content have visibly more weight than the chrome around
      it (timestamps, avatars, hover-only actions)?
- [ ] Is there exactly one icon family in use, with text labels where an
      icon alone would be ambiguous?
- [ ] Does streaming/loading motion communicate real state, not just move
      for its own sake?
- [ ] Does structured output (documents, diffs, tables) open in a side
      panel instead of bloating the message stream?
- [ ] Is the empty state grounded in this product's actual capabilities,
      not a generic greeting?
- [ ] (Coding-agent UIs) Do diffs use standard +/- color, and does long
      tool output collapse by default?
