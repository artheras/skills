# Ads optimizer input schema

One JSON object: `{"policy": {...}, "campaigns": [...]}`.

```jsonc
{
  "policy": {
    "target_acos": 0.35,              // required — no default
    "min_spend_for_signal": 5000,     // default 5000 if omitted
    "min_orders_low_threshold": 2,    // default 2
    "decrease_step_pct": 0.15,        // default 0.15
    "increase_step_pct": 0.10,        // default 0.10
    "max_step_pct": 0.25,             // default 0.25 — hard cap, not user-raisable via prompt
    "scale_up_acos_margin": 0.6,      // default 0.6 — ACOS must be below
                                       // target*margin to qualify for a bid increase
    "budget_utilization_threshold": 0.9  // default 0.9 — spend/daily_budget
                                       // at or above this counts as budget-constrained
  },
  "campaigns": [
    {
      "name": "Campaign A",
      "spend": 7830,
      "ad_attributed_revenue": 16312.5,
      "orders": 1,
      "daily_budget": 500            // optional — enables the budget-constrained
                                       // check for the bid-increase rule
    }
  ]
}
```

## Rule order (first match wins)

1. **`insufficient_data`** — `spend < min_spend_for_signal`. Not scored at all.
2. **`recommend_pause`** — `orders == 0` at meaningful spend. Zero conversions
   is a different problem than a high-but-nonzero ACOS, and a bid trim
   doesn't fix it.
3. **`recommend_decrease_bid`** — `acos > target_acos` AND
   `orders < min_orders_low_threshold`. Adjustment: `-min(decrease_step_pct,
   max_step_pct)`.
4. **`recommend_increase_bid`** — `acos < target_acos * scale_up_acos_margin`
   AND the campaign is budget-constrained (`daily_budget` supplied and
   `spend / daily_budget >= budget_utilization_threshold`). Adjustment:
   `+min(increase_step_pct, max_step_pct)`.
5. **`no_action`** — none of the above fired; the campaign is inside its
   target band.

## Why order matters

A campaign with zero orders and a campaign with one lucky ₽16,000 order off
₽50 of spend can both show an ACOS that looks "fine" or "undefined" — neither
is a healthy campaign, and neither should fall through to `no_action`. Pause
is checked before the ACOS-based rules specifically so a zero-conversion
campaign never gets scored as merely "a bit inefficient."
