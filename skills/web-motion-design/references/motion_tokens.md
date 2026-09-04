# Motion tokens — the `motion` section of `design-tokens.json`

Motion belongs in the **same file** as color, radius, and spacing — the
`design-tokens.json` that `ui-design-system` already defines and validates.
A separate motion config drifts from the design system within a few sessions.

`ui-design-system/scripts/design_tokens.py --validate` checks this section when
present, and `--template` emits it in the skeleton. It is entirely optional: a
token file with no `motion` key stays valid.

```jsonc
{
  "schema_version": "aria.design-tokens.v1",
  "name": "Acme",
  // ... color / radius / spacing / type as defined by ui-design-system ...

  "motion": {
    // Named duration tiers in milliseconds. Chosen by distance and size of
    // what moves — not by how important the content is.
    "duration": {
      "instant": 100,     // press states, toggles, color-only change
      "fast":    150,     // hover, tooltip, small dropdown
      "base":    200,     // menu, popover, in-place transition
      "slow":    300,     // modal, drawer, sheet
      "deliberate": 400   // page transition, first-load orchestration
    },

    // Named easing curves as cubic-bezier control points [x1, y1, x2, y2].
    // Chosen by DIRECTION: entrances decelerate, exits accelerate, on-screen
    // moves ease both ends.
    "easing": {
      "enter":   [0,   0, 0.2, 1],   // ease-out
      "exit":    [0.4, 0, 1,   1],   // ease-in
      "inOut":   [0.4, 0, 0.2, 1],   // ease-in-out
      "standard":[0.4, 0, 0.2, 1]    // alias many systems expect
    },

    // Optional. Declares the reduced-motion policy so the linter can check that
    // a prefers-reduced-motion block exists at all.
    //   "reduce"  — shorten/soften, keep opacity fades (recommended)
    //   "disable" — cut motion to ~0ms
    "reduced_motion": "reduce"
  }
}
```

## Field rules (what `--validate` enforces)

- `motion` is optional; when present it must be an object.
- `motion.duration` values must be **positive numbers in milliseconds**. A value
  `< 1` is flagged as an error — almost always seconds written into a
  millisecond field (`0.3` meaning 300ms), which silently produces a
  near-instant animation rather than a visible one.
- Duration values must be **distinct and strictly increasing when sorted** —
  same rule as `radius` tiers. Two tiers with the same number means one of them
  is not a real tier, and components will pick between them arbitrarily.
- Any duration `> 1000`ms is a **warning**, not an error: legitimate for a
  loading illustration, wrong for a UI transition.
- `motion.easing` values must be arrays of exactly 4 numbers. `x1` and `x2`
  (indices 0 and 2) must be within `[0, 1]` — the CSS spec constrains the time
  axis. `y1`/`y2` may fall outside `[0, 1]`; that is how overshoot/anticipation
  curves are expressed and is valid.
- `motion.reduced_motion`, when present, must be `"reduce"` or `"disable"`.

## Mapping to targets

The tokens are platform-neutral; each target emits its own syntax.

| Token | CSS / Tailwind | SwiftUI | React Native (Reanimated) |
|---|---|---|---|
| `duration.base` | `200ms` / `duration-200` | `.easeInOut(duration: 0.2)` | `withTiming(v, {duration: 200})` |
| `easing.enter` | `cubic-bezier(0,0,0.2,1)` | `.timingCurve(0,0,0.2,1, duration:)` | `Easing.bezier(0,0,0.2,1)` |
| `reduced_motion` | `@media (prefers-reduced-motion)` | `.accessibilityReduceMotion` | `AccessibilityInfo.isReduceMotionEnabled` |

Note the unit change: CSS and RN take **milliseconds**, SwiftUI takes
**seconds**. The token file is the millisecond source of truth; SwiftUI emitters
divide by 1000. Storing seconds in the file to save that division is how you end
up with `0.2` and `200` both appearing in the same codebase.

## Applying tokens in components

```css
:root {
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  --ease-enter: cubic-bezier(0, 0, 0.2, 1);
  --ease-exit:  cubic-bezier(0.4, 0, 1, 1);
}

.dialog {
  transition: opacity var(--duration-slow) var(--ease-enter),
              transform var(--duration-slow) var(--ease-enter);
}
.dialog[data-closing] {
  /* exits shorter than entrances, and accelerating away */
  transition-duration: calc(var(--duration-slow) * 0.7);
  transition-timing-function: var(--ease-exit);
}
```

Two things this example is doing deliberately:

1. **Naming the properties** (`opacity`, `transform`) instead of `all`. `all`
   animates layout properties you never intended and silently picks up any
   property added later.
2. **A shorter, differently-eased exit.** Symmetric enter/exit is the most
   common motion-system mistake — it makes dismissal feel sluggish, because the
   user has already decided and is waiting on the UI to catch up.

## What does NOT belong in motion tokens

- **Per-component keyframes.** Tokens are the vocabulary (durations, curves),
  not the sentences. A spinner's keyframes live with the spinner.
- **Spring configs**, unless the whole system is spring-based. Springs are
  parameterized by stiffness/damping/mass, not duration, and mixing the two
  models in one token file produces components that can't be compared. If the
  project is spring-first, use a `motion.spring` section instead of `duration`
  and say so — do not maintain both.
- **Delays and stagger amounts.** These are composition decisions specific to a
  list or sequence, and hardcoding one stagger value across the system produces
  the exact "everything cascades in" effect that reads as generated.
