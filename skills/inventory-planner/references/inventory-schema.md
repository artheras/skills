# Replenishment input schema

One JSON object: `{"skus": [...]}`. Every entry is one SKU across however
many marketplaces/warehouses it's pooled from — this skill plans stock, it
doesn't care which platform the units eventually sell on.

```jsonc
{
  "review_period_days": 14,        // how far ahead a single reorder should
                                    // cover, on top of the reorder point —
                                    // default 14 if omitted
  "skus": [
    {
      "sku": "OZ-88213",
      "current_stock": 340,
      "daily_sales_velocity": 22.5,  // units/day, recent-window average.
                                      // Omit (or null) if there isn't enough
                                      // sales history yet — the plan will
                                      // refuse to size this SKU rather than
                                      // guess.
      "lead_time_days": 18,          // supplier + freight, to the warehouse.
                                      // Required to compute a reorder point.
      "safety_stock_days": 7,        // buffer beyond lead time; default 7
      "on_order_qty": 0,             // already in transit; omit → flagged
                                      // on_order_unconfirmed, treated as 0
      "moq": 200,                    // optional minimum order quantity
      "unit_cost": 3.4                // optional, for order-value estimate only
    }
  ]
}
```

## Status classification

Computed per SKU as `days_of_cover = current_stock / daily_sales_velocity`
against `reorder_point_days = lead_time_days + safety_stock_days`:

| Status | Meaning |
|---|---|
| `velocity_unavailable` | No usable `daily_sales_velocity` — excluded from sizing, not guessed |
| `lead_time_missing` | No `lead_time_days` — excluded from sizing, not guessed |
| `stockout` | `days_of_cover <= 0` — already out |
| `urgent` | `days_of_cover < lead_time_days` — will run out before a reorder placed today could physically arrive, even ignoring the safety buffer |
| `reorder_now` | `days_of_cover < reorder_point_days` — inside the reorder window |
| `ok` | Comfortably above the reorder point |

## Why refuse instead of estimate

A restock plan that fills in a plausible-looking velocity for a SKU with no
sales history is indistinguishable, on the page, from one built on real data
— until the guess is wrong and the SKU stocks out on schedule anyway. The
honest failure mode here is the same one `execution-position` enforces for
position sizing: no volatility estimate, no vol-target size. Here it's no
sales-velocity estimate, no reorder quantity.
