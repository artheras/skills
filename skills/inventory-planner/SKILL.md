---
name: inventory-planner
description: >-
  Turn current stock, sales velocity, and supplier lead time into a
  replenishment recommendation — which SKUs to reorder, how much, and how
  urgently — never an actual purchase order. Trigger for "备货表",
  "该补多少货", "哪些 SKU 要断货了", "这批要提前多久下单", "restock plan",
  "when should I reorder this SKU", "how much inventory should I order",
  "which products are about to stock out". Do NOT trigger for a one-off
  ERP health check with no forecasting involved (use
  `logistics-warehouse-audit` for that) or for placing/sending a purchase
  order to a supplier — this skill only ever produces a draft plan.
---

# Inventory & Replenishment Planner

A restock recommendation is a forecast wearing a spreadsheet's clothes: it
depends on a sales-velocity estimate, a lead time, and a safety margin, and
every one of those inputs can be wrong or missing. Guessing a plausible
number for a missing input is worse than refusing — a fabricated velocity
looks exactly as confident on the page as a real one, right up until the SKU
stocks out anyway. This skill computes a per-SKU reorder recommendation from
the inputs it actually has, and refuses to size an order for a SKU whose
inputs it doesn't.

This is the forecasting sibling of `logistics-warehouse-audit`
(`enterprise-operations-skills`): that skill checks whether an ERP's current
state looks healthy right now; this one asks whether it will still look
healthy by the time a reorder could arrive.

## Authority boundary (read first)

The output is a `status: "draft"` replenishment plan — a list of suggested
order quantities per SKU, not a purchase order. **Sending or committing an
order to a supplier is never this skill's action** — the same mechanical
boundary `cross-listing` draws around publishing and `execution-position`
draws around live orders. `skill-policy.json` does not list a
PO-submission tool in `allowed_tools`; only read and draft-creation tools are
reachable from this skill.

## Workflow — order matters

1. **Gather inputs per SKU** — current stock, on-hand-in-transit
   (`on_order_qty`), recent sales velocity, supplier lead time, and an
   optional MOQ and unit cost. See `references/inventory-schema.md`.
2. **Refuse to size what you don't know.** No sales-velocity data → the SKU
   is reported `velocity_unavailable`, excluded from the order plan, never
   assigned a guessed reorder quantity. Same for a missing lead time
   (`lead_time_missing`). This mirrors `execution-position`'s refusal to
   size a vol-target position with no volatility estimate.
3. **Run `python scripts/replenishment_plan.py INPUT.json`** (or `--demo`) —
   it computes days-of-cover, a reorder point (lead time + safety buffer),
   and a suggested order quantity per SKU, then classifies each into
   `ok` / `reorder_now` / `urgent` / `stockout` / excluded-for-missing-data.
4. **Round to MOQ, and say so.** A suggested quantity below a declared MOQ is
   rounded up, and the rounding is disclosed (`rounded_to_moq: true`) rather
   than silently shown as the raw computed number.
5. **Check for stock already in transit before recommending more.** If
   `on_order_qty` is absent, the plan proceeds (treating it as 0) but flags
   `on_order_unconfirmed` — double-ordering a SKU that already has a shipment
   inbound is the single most common real-world mistake this skill exists to
   catch.
6. **Present the plan with every flag.** `urgent`/`stockout` SKUs first,
   `velocity_unavailable`/`lead_time_missing` SKUs listed separately as
   "needs data before a recommendation can be made" — never silently dropped
   from the report.
7. Hand the draft plan back for the seller's review and PO decision. Creating
   the draft (a local record, or an explicit "draft PO" tool call on an ERP)
   is fine; submitting it to a supplier is not this skill's job under any
   flag or instruction — see Authority boundary above.

## Guardrails

- No sales-velocity estimate → no reorder quantity for that SKU. Report
  `velocity_unavailable`, do not guess.
- No lead time → no reorder point for that SKU. Report `lead_time_missing`.
- Every suggested quantity is >= 0 and, when a MOQ is declared, rounded up to
  it with the rounding disclosed.
- `on_order_qty` absent is flagged (`on_order_unconfirmed`), not silently
  treated as "definitely zero" without saying so.
- `status` on the output plan is always `draft` — this skill never commits or
  sends a purchase order.
- Unit-cost-based order value is labeled an estimate, never presented as a
  quote.
