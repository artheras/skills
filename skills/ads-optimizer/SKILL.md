---
name: ads-optimizer
description: >-
  Turn raw ad-campaign metrics (spend, attributed revenue, orders) into a
  bid-adjustment recommendation against a declared ACOS target — never an
  autonomous bid change. Trigger for "广告该降价了吗", "这个广告花超了没转化",
  "ACOS 超标怎么办", "review my ad campaigns", "should I lower this bid",
  "which campaigns are burning budget", "ad spend optimization". Do NOT
  trigger for keyword/creative-level ad copy work, and do NOT trigger to
  actually change a live bid or pause a campaign — this skill recommends,
  it never executes.
---

# Ads Optimizer

"The model looks at the dashboard and decides" is not an ads policy, it is a
mood with a chart attached — the same failure `strategy-generation` refuses
for trading strategies. A bid decision here comes from a declared rule
applied to real numbers: an ACOS target the seller set, a minimum spend
before a campaign's data means anything, and a minimum order count before
"low ACOS" and "no conversions" are treated differently. The skill's job is
to name which rule fired and why, in the seller's own numbers, not to feel
out an adjustment.

## Authority boundary (read first)

The output is a **recommendation** — `action`, magnitude, and the plain-
language reason — never a bid change. Calling a bid- or campaign-state-
mutating tool is not this skill's job under any flag or instruction, the same
boundary `cross-listing` draws around publish and `execution-position` draws
around live orders. `skill-policy.json` does not list a mutating ads tool
(`update_campaign_bid`, `pause_campaign`) in `allowed_tools` — the skill has
no way to call one even if instructed to.

## Policy inputs (declared, not assumed)

- `target_acos` — the seller's own ACOS ceiling. There is no sane default;
  this must be supplied.
- `min_spend_for_signal` — a campaign under this spend hasn't produced enough
  data to judge; it is reported `insufficient_data`, not scored.
- `min_orders_low_threshold` — order count below which "not converting" kicks
  in even if ACOS is technically fine (near-zero orders can produce a
  deceptively good ACOS off one lucky sale).
- `decrease_step_pct` / `increase_step_pct` — the adjustment size when a rule
  fires; both capped by `max_step_pct` (default 0.25 — the same
  non-negotiable-via-prompt ceiling `execution-position` puts on Kelly
  sizing, for the same reason: a single aggressive step is how budgets and
  bids get away from a seller).

## Workflow — order matters

1. **Gather campaign metrics** — spend, ad-attributed revenue, orders, and
   (if available) daily budget, for the period being reviewed. See
   `references/ads-schema.md`.
2. **Refuse to score a campaign with too little spend to mean anything** —
   `insufficient_data`, no recommendation, not a guessed one.
3. **Run `python scripts/ads_bid_optimizer.py INPUT.json`** (or `--demo`). It
   applies four rules in order — pause candidate, decrease, increase,
   no-action — and returns one action per campaign with the ACOS, the
   threshold it was checked against, and the reasoning in a sentence a
   seller can read without translation.
4. **Zero orders with meaningful spend recommends pause, not a smaller bid
   cut** — a campaign converting nothing isn't "a bit inefficient," it's not
   working, and a 15% bid trim doesn't fix that.
5. **Present every recommendation with its trigger rule named explicitly** —
   "ACOS 48% > 35% target, orders below threshold → reduce bid 15%," not a
   bare "lower this bid." The seller (or a downstream approval step) is the
   one who actually adjusts the campaign.
6. Nothing in this workflow calls a mutating ads tool. If the runtime offers
   an "apply this recommendation" action outside this skill, that action —
   not this skill — is what needs the human sign-off.

## Guardrails

- No recommendation without `target_acos` declared — this skill does not
  assume a target.
- Spend below `min_spend_for_signal` → `insufficient_data`, never scored.
- Zero orders at meaningful spend → `recommend_pause`, not a bid-decrease.
- Every step magnitude is capped at `max_step_pct` (default 0.25),
  non-negotiable via prompt.
- No mutating ads tool is reachable from this skill — the refusal to execute
  is structural, declared in `skill-policy.json`, not just written guidance.
