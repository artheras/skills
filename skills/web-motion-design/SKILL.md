---
name: web-motion-design
description: >-
  Design and implement the *motion* layer of a UI — entrance/exit transitions,
  hover and press feedback, loading and skeleton states, scroll-driven reveals,
  page transitions, and the duration/easing scale that keeps them coherent.
  Trigger for "加点动效", "这个页面太生硬了", "加个过渡动画", "hover 效果",
  "make this feel smoother", "add animation to this component", "page transition",
  "scroll reveal", "微交互", "loading 动画", "为什么我的动画很卡", or whenever a
  built UI is functionally correct but reads as static, abrupt, or janky. Also
  trigger when reviewing motion someone already wrote — over-animation is the
  more common failure, and cutting animation is a valid outcome of this skill.
  Do NOT trigger to choose colors/type/layout from scratch (use
  `industry-design-direction` for direction, `ui-design-system` for tokens) or
  to build a category's static structure (`terminal-software-design`,
  `conversational-ui-restraint`, `trading-ui-patterns`). Motion is the last
  layer, applied to a UI that already works without it.
  Portable: self-contained prose, no script dependency.
---

# Web Motion Design

Motion is the only design layer that costs the user *time*. A color choice is
free to look at; a 600ms transition is 600ms they cannot act. That asymmetry is
the whole discipline: **every animation must buy back the time it spends**, by
explaining a change the user would otherwise have to re-scan for.

This skill covers the motion layer only. It assumes the UI already works
statically — if it doesn't, animation will not save it, and adding motion to
hide a layout problem makes the problem harder to see.

## The one rule that catches most bad AI motion

> If you cannot say what the animation *tells* the user, delete it.

The generic-AI-motion signature is decoration without information: a hero that
fades up on load, cards that stagger in for no reason, a gradient that pans
forever, everything at `transition: all 0.3s ease`. None of it answers "what
changed and where did it come from" — it just delays the content. The tell is
that you could remove every one of those animations and lose nothing but time.

Motion that earns its place answers one of exactly four questions:

| Question | Motion that answers it |
|---|---|
| **Where did this come from?** | A panel slides from the edge it's anchored to; a modal scales from the button that opened it |
| **Where did it go?** | A deleted row collapses its own height; a dismissed toast exits toward its trigger |
| **Did my input register?** | Press-down scale, hover lift, toggle knob travel — under 150ms, always |
| **Is the system working?** | Skeletons, progress, streaming cursors — anything covering real latency |

Anything that answers none of these is decoration. Decoration is not
automatically wrong — a landing page's hero may legitimately want personality —
but it must be a deliberate choice you can defend, not a default.

## Duration: pick from a scale, never a vibe

Duration follows the *distance and size* of what moves, not the importance of
the content. Big things moving far need longer; small things need to feel
instant.

| Tier | Duration | What it's for |
|---|---|---|
| `instant` | 100ms | Press states, checkbox/toggle, color-only changes |
| `fast` | 150ms | Hover, tooltips, small dropdowns, icon swaps |
| `base` | 200ms | Menus, popovers, most in-place transitions |
| `slow` | 300ms | Modals, drawers, sheets, anything covering the viewport |
| `deliberate` | 400ms | Full page transitions, first-load orchestration |

Above 400ms a UI transition reads as slow regardless of how good the easing is.
If something genuinely needs longer, it is an *animation* (a loading illustration,
a celebration), not a transition, and it must not block interaction.

Scale with distance, not with importance: an element traveling 400px can take
~1.5× the duration of one traveling 100px. A "very important" modal does not get
a slower animation — it gets a clearer one.

## Easing: three curves, chosen by direction

The single most common motion mistake in generated code is `ease` or `linear`
on everything. Linear motion looks mechanical because nothing in the physical
world starts and stops at constant velocity.

- **Entering** the screen → **ease-out**: `cubic-bezier(0, 0, 0.2, 1)`
  Fast on arrival, gentle landing. The element is already on its way when you
  first see it, so it feels responsive.
- **Leaving** the screen → **ease-in**: `cubic-bezier(0.4, 0, 1, 1)`
  Gentle start, accelerating away. Nobody needs to watch an exit finish, so
  exits should be ~30% shorter than the matching entrance.
- **Moving/resizing on screen** → **ease-in-out**: `cubic-bezier(0.4, 0, 0.2, 1)`
  Smooth at both ends because the user tracks the element the whole way.

Spring physics (Framer Motion's `type: "spring"`, iOS defaults) is a legitimate
alternative for direct-manipulation UI — dragging, sheets that follow a finger —
where the user's gesture should feel physically connected. For ordinary
state transitions, a tuned cubic-bezier is more predictable and cheaper.

## Performance: animate two properties, not twenty

The browser can animate `transform` and `opacity` on the compositor without
recalculating layout or repainting. Everything else — `width`, `height`, `top`,
`left`, `margin`, `padding` — forces layout on every frame and is where jank
comes from.

- Move → `transform: translate()`, never `top`/`left`
- Resize → `transform: scale()`, never `width`/`height`
- Reveal → `opacity`, plus `transform` for direction
- **Never write `transition: all`.** It animates properties you didn't intend
  (often layout ones), and it silently animates future properties too.
- `will-change` is a targeted fix for a measured problem, not a prophylactic.
  Applied broadly it costs memory and can make things worse.

Height animation is the notable hard case (accordions, expanding rows). Real
options: animate `max-height` to a known value, use `grid-template-rows: 0fr → 1fr`,
or measure and animate `transform: scaleY()` with a counter-scaled child. Pick
one deliberately; there is no free version.

## Accessibility: `prefers-reduced-motion` is not optional

For users with vestibular disorders, large motion causes real physical symptoms.
The setting is a medical accommodation.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

That blanket reset is the safe floor, but the better treatment is to **reduce,
not remove**. The information motion carries still needs to arrive: keep opacity
fades (they don't trigger vestibular response), drop travel and scale, kill
parallax and autoplay entirely. A modal that fades in without sliding still
answers "something new appeared."

Also: never convey state through motion alone. A pulsing dot that means "live"
must also differ in color or carry a label.

## Reviewing motion someone already wrote

Cutting is the most common correct outcome. Look for:

- **Everything animates.** If every element on the page has a transition, none
  of them signal anything. Motion works by contrast with stillness.
- **Entrance animations on content the user came to read.** Making someone wait
  400ms to read text they navigated to is a tax, not a delight.
- **Scroll-triggered reveals below the fold.** They fire on content the user is
  actively scrolling toward — the reveal lands *after* they're already looking.
  Use sparingly and with short durations.
- **Looping animation near text.** Anything moving continuously beside content
  competes for the same attention the content needs.
- **Exit animations the same length as entrances.** Exits should be shorter.
- **Motion that blocks input.** A user should be able to click through a
  transition. If a 300ms modal animation swallows a click at 100ms, that's a bug.

## Store motion in the design system, not in components

If this project uses `ui-design-system`'s `design-tokens.json`, motion belongs in
the same file as a `motion` section — durations and easings named, so a component
never hardcodes `0.3s ease`. Consistency in motion is as visible as consistency
in color: three different durations for the same interaction across three screens
reads as three different products.

See `references/motion_tokens.md` for the schema, the CSS/SwiftUI/React Native
mapping, and how the `ui-design-system` validator checks it.

## Framework notes

- **CSS transitions** — correct default for state changes. Reach for a library
  only when you need orchestration, gestures, or exit animations.
- **Framer Motion / Motion** (React) — the reason to adopt it is `AnimatePresence`
  (exit animations, which CSS cannot do when the element unmounts) and layout
  animation. If you're only doing hover states, it's weight you don't need.
- **GSAP** — earns its place for scroll-driven timelines and complex sequencing.
  Overkill for component-level UI.
- **View Transitions API** — increasingly the right answer for page/route
  transitions; degrades gracefully where unsupported. Check current browser
  support before committing to it as the only path.
- **Lottie** — for designer-authored illustration, not UI state. Do not ship a
  Lottie file to animate a button.
