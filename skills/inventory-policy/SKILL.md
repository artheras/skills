---
name: inventory-policy
description: >-
  Work out when and how much to reorder, and what stock is stuck, for a
  warehouse or 3PL shipper from actual demand history and lead times. Trigger
  for "补货点怎么算", "安全库存设多少", "该补多少货", "哪些货要补", "呆滞库存",
  "库存周转", "ABC 分类", "reorder point", "safety stock", "how much should we
  order", "dead stock", "slow movers", or whenever the user supplies SKU
  stock levels with sales/outbound history and asks what to replenish. Also
  fire for a 3PL asking this on behalf of one client (货主). Do NOT trigger for
  carrier or freight-cost questions (that is carrier-scorecard), for demand
  forecasting of new products with no history, or for warehouse layout.
---

# Inventory Policy

Replenishment advice moves money, so it has to come from formulas a planner
can recompute — not from a sense of what "looks low". This skill computes
reorder points, safety stock and order quantities from the shipper's own
demand history and lead times, classifies the portfolio (ABC/XYZ), finds dead
and slow stock, and refuses to produce a policy where the history cannot
support one.

## Principles

1. **One shipper at a time.** A 3PL holds many clients' stock. Never pool two
   shippers' SKUs into one analysis or one table: that hands one client's
   commercial data to another. If the data carries `owner_id` for more than one
   shipper, run per shipper with `--owner`. Use `--all-owners` only when the
   user is the 3PL itself asking for an internal view, and keep the
   "not for client distribution" marker on anything you produce from it.
2. **No history, no policy.** Under 14 days of demand history, the script
   reports `insufficient_history` instead of a reorder point. Say so; do not
   fill the gap with an estimate of your own.
3. **Variability is the point.** Safety stock covers demand *and* lead-time
   variability: z·√(L·σ_d² + d̄²·σ_L²). If the user has lead-time spread,
   ask for it — leaving σ_L at 0 understates safety stock.
4. **State what is not modelled.** Capacity, MOQs, case packs and supplier
   terms are outside the formula. A suggested quantity must be presented with
   that caveat, not as a purchase order.

## Workflow — order matters

1. Get per-SKU records: `sku`, `on_hand`, `lead_time_days`, `daily_demand`
   (daily outbound quantities, oldest first). Optional: `owner_id`,
   `on_order`, `backorder`, `lead_time_std_days`, `unit_cost` (needed for ABC),
   `days_since_last_movement`.
2. Ask for the target service level if the user has one (default 95%) and the
   review cycle in days (default 7).
3. Run the script:
   `python scripts/inventory_policy.py --skus skus.csv --owner <shipper>`
4. Report, in this order: SKUs to reorder (quantity, reorder point, days of
   cover), SKUs with insufficient history, dead and slow stock, then the ABC/XYZ
   picture. Quote the `assumptions` block verbatim at the end.
5. Never round the script's numbers further, and never present a quantity
   without the caveat in principle 4.

## Bundled resources

- `scripts/inventory_policy.py` — the computation. Standard library only.
  `python scripts/inventory_policy.py --demo` checks hand-computed reference
  values (safety stock 18, reorder point 78, order 133) and shipper isolation.
- `references/formulas.md` — read when the user asks why a number is what it
  is, or wants to change a threshold.
- `agents/openai.yaml` — the human-facing entry point.
