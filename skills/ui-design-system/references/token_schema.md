# design-tokens.json — platform-neutral schema

One file, owned by the user, that every UI they generate must resolve against.
Values are platform-neutral; each target (CSS, SwiftUI, RN, Flutter) maps them
into its own syntax. `scripts/design_tokens.py --template` prints a fillable
skeleton; `--validate` checks a filled one.

```jsonc
{
  "schema_version": "aria.design-tokens.v1",
  "name": "Acme",                    // the user's system name (required)
  "appearance": "light-dark",        // "light-dark" (dual) or "single"
  "conventions": {
    "emoji_icons": "forbid"          // "forbid" (default) | "allow"
  },
  "color": {
    // For appearance "single": a hex string. For "light-dark": {light, dark}.
    "canvas":        { "light": "#FAF9F8", "dark": "#0F1216" },  // screen bg
    "surface":       { "light": "#FFFFFF", "dark": "#171B21" },  // card bg
    "textPrimary":   { "light": "#0F1216", "dark": "#F2EFE9" },
    "textSecondary": { "light": "#5A5F66", "dark": "#A8ADB4" },
    "border":        { "light": "#E7E4E0", "dark": "#2A2E34" },
    "accent":        { "light": "#2F6BFF", "dark": "#5B86FF" }
    // ...any number of named colors the user's system needs
  },
  "radius": {                        // named tiers, values in pt/px
    "chip": 6, "control": 8, "card": 12, "sheet": 16, "hero": 20
  },
  "spacing": {
    "base": 4,                       // smallest grid unit; steps are multiples of it
    "steps": { "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32 }
  },
  "type": {                          // named roles
    "title":    { "size": 22, "weight": 600, "mono": false },
    "body":     { "size": 15, "weight": 400, "mono": false },
    "caption":  { "size": 11, "weight": 400, "mono": false },
    "priceHero":{ "size": 40, "weight": 700, "mono": true }
  },
  "stroke": { "hairline": 0.5, "border": 1 },

  // Optional. The motion layer — duration tiers (ms) and easing curves — so
  // animation is part of the design system rather than hardcoded per component.
  // Owned by the `web-motion-design` skill; full schema, rules, and the
  // CSS/SwiftUI/RN mapping live in that skill's references/motion_tokens.md.
  // Validated here when present; omit the key entirely and it is skipped.
  "motion": {
    "duration": { "instant": 100, "fast": 150, "base": 200, "slow": 300, "deliberate": 400 },
    "easing": {
      "enter": [0, 0, 0.2, 1],      // ease-out  — things arriving
      "exit":  [0.4, 0, 1, 1],      // ease-in   — things leaving
      "inOut": [0.4, 0, 0.2, 1]     // ease-in-out — moving on screen
    },
    "reduced_motion": "reduce"      // "reduce" | "disable"
  },

  // Optional: declares which text colors sit on which surface, so the
  // validator can check WCAG contrast. Omit and contrast is skipped.
  "contrast_pairs": [
    { "text": "textPrimary",   "on": "canvas",  "min": 4.5 },
    { "text": "textSecondary", "on": "canvas",  "min": 4.5 },
    { "text": "textPrimary",   "on": "surface", "min": 4.5 }
  ]
}
```

## Field rules (what `--validate` enforces)

- `name`, `appearance`, `color` are required; `appearance` must be
  `light-dark` or `single`, and every `color` value must match that mode
  (dual object vs single hex).
- Every color value is a `#RRGGBB` hex (case-insensitive). This is the canonical
  form the linter normalizes literals to before comparing.
- `radius` values (if present) must be a strictly increasing scale when sorted —
  a set of distinct tiers, not two tiers with the same number.
- `spacing.steps` (if present) must each be a multiple of `spacing.base`, and
  strictly increasing when sorted.
- `motion` (if present): `duration` values are positive **milliseconds** and must
  be distinct — a value under 1 is rejected as seconds written into a
  millisecond field (`0.3` meaning 300ms silently produces an invisible
  animation), and anything over 1000ms warns. `easing` values are 4-number
  cubic-bezier arrays whose **x** control points (indices 0 and 2) sit within
  `[0,1]`; y may fall outside, which is how overshoot curves are expressed.
- `contrast_pairs` (if present): each `text` and `on` must name a real color;
  the validator computes WCAG 2.1 relative-luminance contrast for **both**
  light and dark and flags any below `min` (default 4.5 for body text, use 3.0
  for large/bold per WCAG AA).

## Mapping to targets (the linter is target-aware, the tokens are not)

The same token file drives any target; only the emitted syntax differs:

| Token | CSS / Tailwind | SwiftUI | React Native |
|---|---|---|---|
| `color.accent` | `var(--accent)` / `bg-accent` | `Color("accent")` (asset) | `theme.accent` |
| `radius.card` | `border-radius: 12px` | `.cornerRadius(Radius.card)` | `borderRadius: radius.card` |
| `spacing.lg` | `padding: 16px` | `.padding(Space.lg)` | `padding: space.lg` |

`design_lint.py` recognizes off-system **literals** in each of these syntaxes
(hex strings, `Color(red:g:b:)`, `rgb()/rgba()`, numeric `cornerRadius`/
`border-radius`/`borderRadius`) and compares them against the values declared
in the user's file. Anything not in the file is "off-system".
