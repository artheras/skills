---
name: carrier-scorecard
description: >-
  Compare carriers by lane and find freight overcharges and savings from actual
  waybills. Trigger for "哪家快递/物流更好", "承运商评分", "运费是不是贵了",
  "运费异常", "怎么降运费", "准时率", "换哪家承运商", "carrier scorecard",
  "freight audit", "which carrier is cheaper", "on-time performance",
  "are we overcharged", or whenever the user supplies waybills/shipments with
  carrier, cost and delivery status and asks which carrier to use or where
  money is leaking. Also fire for a 3PL doing this for one client (货主). Do NOT
  trigger for tracking a single parcel's location, for inventory/replenishment
  questions (that is inventory-policy), or for building a rate card from
  carrier quotes with no shipment history.
---

# Carrier Scorecard

"Carrier A is 100% on time" is meaningless when A carried one parcel. This
skill ranks carriers within each lane by what the evidence supports, flags
freight charges that stand out from the lane, and estimates savings only where
switching would not trade money for reliability.

## Principles

1. **One shipper at a time.** Never pool two shippers' waybills into one
   scorecard: rates and volumes are a client's commercial data. Run per
   shipper with `--owner`. `--all-owners` is for the 3PL's own carrier
   negotiations only, and its output stays marked not for client distribution.
2. **Rank by the lower bound, not the rate.** Carriers are ranked by the 95%
   Wilson lower bound of their on-time rate: 1/1 on time scores 0.21, 98/100
   scores 0.93. Carrier-lanes under the minimum shipment count are shown but
   not ranked — say so rather than ranking them anyway.
3. **Compare like with like.** Rankings, anomalies and savings are within one
   lane (origin → destination). Never compare a carrier's price on one lane
   with another lane's.
4. **A saving must not cost reliability.** A switch is only suggested when the
   alternative is cheaper per kg *and* at least as reliable. The estimate is
   volume × rate difference; contract terms, surcharges, minimums and capacity
   are not modelled, and the answer must say so.
5. **An anomaly is a question, not an accusation.** Flagged waybills are for
   checking — dimensional weight, remote-area surcharges and re-weighs explain
   many. Phrase them as "verify", never as "overcharged".

## Workflow — order matters

1. Get waybills: `carrier`, `total_cost`, and for useful results `origin`,
   `destination`, `billed_weight_kg`, `is_on_time`. Optional: `owner_id`,
   `actual_weight_kg`, `has_exception`, `waybill_no`.
2. Run the script:
   `python scripts/carrier_scorecard.py --waybills waybills.csv --owner <shipper>`
3. Report per lane: the ranked carriers (on-time rate *with* its lower bound,
   median cost/kg, shipments), then savings, then anomalies to verify. Quote
   the `assumptions` block at the end.
4. If most carrier-lanes are unranked, say the data is too thin to rank, and
   how many more shipments would change that.

## Bundled resources

- `scripts/carrier_scorecard.py` — the computation. Standard library only.
  `python scripts/carrier_scorecard.py --demo` checks hand-computed reference
  values: the Wilson bounds above, a 900 saving on the reference lane, and an
  overcharge on a contracted lane where the median absolute deviation is 0.
- `references/formulas.md` — read when the user asks how a ranking or flag was
  decided, or wants a different threshold.
- `agents/openai.yaml` — the human-facing entry point.
