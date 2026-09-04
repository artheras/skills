---
name: competitor-monitor
description: >-
  Turn a competitor's price, inventory-proxy, search rank, and review-velocity
  changes into named, hedged inferences about what they might be doing —
  clearing stock, running ads, heading toward a stockout — never a confirmed
  statement of their strategy. Trigger for "对手是不是在降价冲销量",
  "竞品排名突然涨了", "这个竞品是不是要断货了", "why did this competitor's
  rank jump", "is this competitor clearing inventory", "competitor price drop
  analysis". Do NOT trigger for a single-field price check with no other
  signal available (that's just a lookup, not a monitoring inference), and
  do NOT trigger to make a pricing or ad-spend decision on the seller's own
  listings — that decision belongs to `ads-optimizer`/the seller, informed by
  this skill's output, not made by it.
---

# Competitor Monitor

A single signal lies constantly: a price drop alone is a promotion, a
clearance, or a pricing-algorithm blip, and there's no way to tell which from
price data alone. This skill never infers from one signal — every pattern it
names requires two or more signals moving together (price, an inventory
proxy, search rank, review velocity), and even then the output is a hedged
correlation, not a claim about what the competitor is actually doing. Nobody
outside that competitor's own systems knows their real inventory or intent;
this skill is explicit about working from proxies for exactly that reason.

## Authority boundary (read first)

Every output is a **named pattern match against declared thresholds**, with
the phrase "consistent with" rather than "is" — `clearance_push` means the
observed deltas are consistent with a clearance push, not that one is
confirmed. This skill has no opinion on what the seller should do to their
own listings; it hands a labeled read of a competitor's public signals to the
seller (or to `ads-optimizer`, `cross-listing` etc.) to act on. It never
calls a tool that changes the seller's own price, bid, or listing.

## Signals (all proxies — say so)

- **`price`** — the competitor's observed price, current vs. prior.
- **`inventory_proxy`** — an estimate of stock (e.g. in-stock listing count,
  a "only N left" style signal, or a modeled availability score) — never the
  competitor's real inventory, which no outside party can see.
- **`rank`** — search/category rank, lower number is better; `rank_change`
  is `prior - current` so a positive number means the competitor improved.
- **`reviews_gained`** — new reviews within the observation window for the
  current and prior windows, used to derive a velocity ratio. A competitor
  with zero prior-window reviews and any current-window reviews is flagged
  `new_review_activity` rather than given a division-by-zero ratio.

## Workflow — order matters

1. **Gather two-period signals per competitor** — see
   `references/signal-schema.md`. A competitor with fewer than two signal
   types available gets `no_clear_pattern` — this skill does not infer from
   a single moving number.
2. **Run `python scripts/pattern_match.py INPUT.json`** (or `--demo`) — it
   computes the deltas, tests them against six named patterns
   (`references/pattern-catalog.md`), and returns every pattern that
   matches (patterns are not mutually exclusive — a competitor can be
   consistent with more than one story) plus a suggested monitoring
   posture, never a pricing instruction for the seller's own listings.
3. **Zero matches is a valid, honest result** (`no_clear_pattern`) — present
   the raw deltas rather than forcing a narrative onto ambiguous signals.
4. **Rank competitors by how many signals moved, not by how dramatic the
   story sounds** — a competitor matching three corroborating patterns
   deserves more attention this period than one with a single large but
   isolated price move.
5. **Hand the labeled read to whichever skill or human owns the actual
   decision.** `stockout_risk` on a competitor is a share opportunity;
   `clearance_push` might argue for holding price and watching, not
   matching it — see the response postures in
   `references/pattern-catalog.md`. This skill states the read, not the
   response.

## Guardrails

- No pattern without at least two corroborating signals moving together.
- Every match is phrased as "consistent with," never "is" or "confirmed."
- `inventory_proxy` is always labeled a proxy, never presented as the
  competitor's actual stock level.
- Zero prior-window reviews with current-window reviews present is
  `new_review_activity`, never a fabricated velocity ratio (division by
  zero disguised as a number).
- This skill never calls a tool that changes the seller's own price, bid,
  or listing — it reads a competitor's signals and stops there.
