---
name: profit-engine
description: >-
  Roll up revenue minus every real cost bucket (COGS, platform commission,
  advertising, logistics, warehousing, returns, refunds, payment fees,
  penalties, FX impact, tax) into net profit per store, and explain a
  period-over-period profit change bucket by bucket. Trigger for "这个月净利润",
  "为什么GMV涨了利润却跌了", "多店利润汇总", "利润是从哪掉的",
  "monthly net profit", "why did profit drop while revenue grew",
  "profit bridge", "which cost is eating my margin". Do NOT trigger for a
  single already-known P&L figure with no bucket breakdown requested, and
  do NOT trigger for tax filing or statutory accounting — this produces an
  operating profit view for the seller, not a compliance document.
---

# Profit Engine

`revenue - COGS` is not a profit number, it is a rumor. The real answer needs
platform commission, ad spend, logistics, warehousing, returns, refunds,
payment processing fees, penalties, FX movement, and tax all in the same
ledger — and the moat isn't the subtraction, it's refusing to subtract a cost
bucket nobody actually supplied. Reporting a clean profit number built by
treating a missing ad-spend feed as zero cost is not optimism, it is the
single most common way a seller's own dashboard lies to them: GMV up 18%,
"profit" up too, because the platform's rising ad bill just wasn't in the
number.

## Authority boundary (read first)

This skill produces a **profit report**, not an accounting filing and not a
tax position. It has no opinion on statutory treatment, depreciation
schedules, or filing deadlines — a missing or wrong number here costs a
seller a bad decision, not a compliance violation, and it should never be
handed to a tax authority as-is.

## Workflow — order matters

1. **Gather per-store, per-period cost buckets** — revenue and all ten cost
   lines, for the current period and the comparison (prior) period. See
   `references/profit-schema.md`.
2. **Refuse to zero-fill a missing bucket.** A cost bucket that wasn't
   supplied is `null`, not `0` — filling it with zero always moves reported
   profit in the flattering direction (higher), which is exactly the error
   a seller least wants from this tool. A store with any missing bucket gets
   `profit_incomplete: true` and its net profit reported as an **upper
   bound**, not a number.
3. **Run `python scripts/profit_waterfall.py INPUT.json`** (or `--demo`) — it
   computes net profit per store, then a **bridge**: the profit change
   between periods decomposed into a revenue-change term and one term per
   cost bucket, ranked by how much of the change each one explains.
4. **Lead with the bridge, not the total.** "Net profit is ¥X" answers the
   wrong question when the real ask is "why did it move." The largest
   magnitude line in the bridge is the headline, e.g. "advertising spend
   explains 42% of this month's profit decline, more than the revenue gain
   offset."
5. **Reconcile.** `revenue_change - sum(cost_bucket_changes)` must equal
   `profit_change` when both periods are complete for a store — the script
   checks this and flags `bridge_mismatch` if it doesn't, which usually means
   an FX or currency-normalization inconsistency between periods rather than
   a real business change.
6. **Roll up across stores** only from stores with complete data in both
   periods; incomplete stores are reported separately with their upper bound,
   never blended into a portfolio total that would silently understate the
   real cost base.

## Guardrails

- Missing cost bucket → `null` input, `profit_incomplete: true` output, net
  profit reported as an upper bound — never zero-filled.
- All-zero cost buckets for a store are flagged `suspiciously_clean` (WARN) —
  more often an unrecorded feed than a genuinely cost-free store.
- Portfolio-level totals only include stores with complete data in both
  periods; incomplete stores are listed, not folded in.
- The bridge decomposition must reconcile to the reported profit change for
  any store with complete data in both periods, or it is flagged, not hidden.
- This is an operating-profit view, not a tax or statutory filing — never
  represented as one.
