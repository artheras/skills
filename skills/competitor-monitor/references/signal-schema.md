# Competitor signal input schema

One JSON object: `{"policy": {...}, "competitors": [...]}`.

```jsonc
{
  "policy": {
    "price_drop_threshold": -0.05,     // default -0.05 (a 5% drop or more)
    "price_flat_band": 0.03,           // default 0.03 — within +/-3% counts as "unchanged"
    "inventory_drop_threshold": -0.15, // default -0.15
    "inventory_up_threshold": 0.15,    // default 0.15
    "rank_improve_threshold": 5,       // default 5 positions
    "rank_decline_threshold": -5,      // default -5 positions
    "review_velocity_up_threshold": 1.5,   // default 1.5x
    "review_velocity_down_threshold": 0.67 // default 0.67x
  },
  "competitors": [
    {
      "name": "Competitor X",
      "price": {"current": 890, "prior": 1000},
      "inventory_proxy": {"current": 66, "prior": 100},
      "rank": {"current": 23, "prior": 50},
      "reviews_gained": {"current": 34, "prior": 10}
    }
  ]
}
```

Any signal object may be omitted entirely if it isn't available for a
competitor this period — the pattern matcher scores whatever signals it has
and never fabricates a missing one.

## Field semantics

- **`rank`** — lower is better (position 1 beats position 50).
  `rank_change = prior - current`, so a positive `rank_change` means the
  competitor's rank improved.
- **`reviews_gained`** — new reviews *within* the observation window, not a
  cumulative total. `reviews_gained.prior == 0` with `reviews_gained.current
  > 0` is reported `new_review_activity`, not a computed ratio (dividing by
  zero to get a "velocity" is a fabricated number wearing a formula).
- **`inventory_proxy`** — whatever availability signal is actually
  observable (in-stock listing count, a marketplace's own "only N left"
  display, a modeled score). It is never the competitor's real stock level,
  and every output that references it says "proxy" for that reason.
