#!/usr/bin/env python3
"""
pattern_match.py — competitor signal deltas -> named, hedged pattern matches.

Converts raw price/inventory-proxy/rank/review deltas into zero or more named
patterns (see references/pattern-catalog.md), each requiring at least two
signals moving together — never a verdict from a single number, and never a
claim stronger than "consistent with":

  deltas       : price_change_pct, inventory_change_pct, rank_change
                 (prior - current, positive = improved), review_velocity_ratio
                 (current/prior reviews-gained, or new_review_activity when
                 prior is 0 and current isn't — never a fabricated ratio)
  patterns     : clearance_push, aggressive_ad_push, stockout_risk,
                 price_war_signal, fading_listing, restock_recovery — all
                 tested, all matches returned (not mutually exclusive)
  no signal    : zero patterns matched is a valid, honest result
                 (no_clear_pattern), not something the script tries to force

This script never touches a pricing or ad-spend tool — it reads signals and
names correlations, nothing else.

Input: a single JSON file (see references/signal-schema.md):
  policy{...threshold overrides...}
  competitors[]: name, price?, inventory_proxy?, rank?, reviews_gained?
                 (each a {current, prior} pair; any may be omitted)

Try it with no data:  python pattern_match.py --demo
The demo runs the skill's own worked example (price down 11%, inventory
proxy down 34%, rank improved 27 positions, review velocity up 3.4x ->
clearance_push) plus a stockout-risk competitor and a genuinely ambiguous
one with only a single signal available (no inference attempted).

Stdlib only — runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys

DEFAULT_POLICY = {
    "price_drop_threshold": -0.05,
    "price_flat_band": 0.03,
    "inventory_drop_threshold": -0.15,
    "inventory_up_threshold": 0.15,
    "rank_improve_threshold": 5,
    "rank_decline_threshold": -5,
    "review_velocity_up_threshold": 1.5,
    "review_velocity_down_threshold": 0.67,
}


def _pct_change(current, prior):
    if prior in (0, None) or current is None:
        return None
    return round((current - prior) / prior, 4)


def compute_deltas(competitor: dict) -> dict:
    deltas: dict = {}

    price = competitor.get("price")
    if price and price.get("prior") not in (0, None) and price.get("current") is not None:
        deltas["price_change_pct"] = _pct_change(price["current"], price["prior"])

    inv = competitor.get("inventory_proxy")
    if inv and inv.get("prior") not in (0, None) and inv.get("current") is not None:
        deltas["inventory_change_pct"] = _pct_change(inv["current"], inv["prior"])

    rank = competitor.get("rank")
    if rank and rank.get("current") is not None and rank.get("prior") is not None:
        deltas["rank_change"] = rank["prior"] - rank["current"]

    reviews = competitor.get("reviews_gained")
    if reviews and reviews.get("current") is not None:
        prior_reviews = reviews.get("prior")
        if prior_reviews in (0, None) and reviews["current"] > 0:
            deltas["new_review_activity"] = True
        elif prior_reviews:
            deltas["review_velocity_ratio"] = round(reviews["current"] / prior_reviews, 2)

    return deltas


def _review_velocity_up(deltas: dict, policy: dict) -> bool:
    if deltas.get("new_review_activity"):
        return True
    ratio = deltas.get("review_velocity_ratio")
    return ratio is not None and ratio >= policy["review_velocity_up_threshold"]


def _review_velocity_down(deltas: dict, policy: dict) -> bool:
    ratio = deltas.get("review_velocity_ratio")
    return ratio is not None and ratio <= policy["review_velocity_down_threshold"]


def match_patterns(deltas: dict, policy: dict) -> list[dict]:
    price = deltas.get("price_change_pct")
    inv = deltas.get("inventory_change_pct")
    rank = deltas.get("rank_change")

    price_down = price is not None and price <= policy["price_drop_threshold"]
    price_flat = price is not None and abs(price) <= policy["price_flat_band"]
    price_not_down = price is not None and price > -policy["price_flat_band"]
    inv_down = inv is not None and inv <= policy["inventory_drop_threshold"]
    inv_not_down = inv is not None and inv > policy["inventory_drop_threshold"]
    inv_flatish = inv is not None and inv >= -policy["price_flat_band"]
    inv_up = inv is not None and inv >= policy["inventory_up_threshold"]
    rank_improved = rank is not None and rank >= policy["rank_improve_threshold"]
    rank_declined = rank is not None and rank <= policy["rank_decline_threshold"]

    matches = []

    if price_down and inv_down and rank_improved:
        matches.append({
            "pattern": "clearance_push",
            "signals": ["price_down", "inventory_down", "rank_improved"],
            "reading": "consistent with discounting to clear stock while gaining rank from the resulting sales",
            "monitoring_posture": "hold price; watch for a restock signal before assuming this is permanent",
        })

    if rank_improved and _review_velocity_up(deltas, policy) and price_flat:
        matches.append({
            "pattern": "aggressive_ad_push",
            "signals": ["rank_improved", "review_velocity_up", "price_flat"],
            "reading": "consistent with increased ad spend or promotion placement without discounting",
            "monitoring_posture": "monitor shared-keyword auction pressure; no price action implied",
        })

    if inv_down and price_not_down and rank_declined:
        matches.append({
            "pattern": "stockout_risk",
            "signals": ["inventory_down", "price_not_down", "rank_declined"],
            "reading": "consistent with running low on stock — falling rank likely reflects marketplace "
                       "deprioritization of a low-stock listing, not falling demand",
            "monitoring_posture": "no defensive action needed — usually a share opportunity, watch for their restock",
        })

    if price_down and inv_not_down:
        matches.append({
            "pattern": "price_war_signal",
            "signals": ["price_down", "inventory_not_down"],
            "reading": "a price cut not paired with a clearance signal — could be a temporary promotion "
                       "or a sustained repricing",
            "monitoring_posture": "verify it isn't a time-boxed promotion before matching the price",
        })

    if rank_declined and _review_velocity_down(deltas, policy) and inv_flatish:
        matches.append({
            "pattern": "fading_listing",
            "signals": ["rank_declined", "review_velocity_down", "inventory_flat_or_up"],
            "reading": "consistent with losing visibility or buyer interest while stock is available",
            "monitoring_posture": "low priority for monitoring bandwidth this period",
        })

    if inv_up and price_flat:
        matches.append({
            "pattern": "restock_recovery",
            "signals": ["inventory_up", "price_flat"],
            "reading": "consistent with recovering from a low-stock period",
            "monitoring_posture": "re-evaluate defensive posture — the opportunity window may be closing",
        })

    return matches


def evaluate_competitor(competitor: dict, policy: dict) -> dict:
    deltas = compute_deltas(competitor)
    signal_count = sum(1 for k in ("price_change_pct", "inventory_change_pct", "rank_change") if k in deltas) \
        + (1 if ("review_velocity_ratio" in deltas or "new_review_activity" in deltas) else 0)

    if signal_count < 2:
        return {"competitor": competitor.get("name", "unnamed"), "deltas": deltas,
                "patterns": [], "pattern": "no_clear_pattern",
                "note": "fewer than two signals available — no inference attempted"}

    matches = match_patterns(deltas, policy)
    return {
        "competitor": competitor.get("name", "unnamed"),
        "deltas": deltas,
        "patterns": matches,
        "pattern": matches[0]["pattern"] if matches else "no_clear_pattern",
        "signal_count": signal_count,
    }


def evaluate(payload: dict) -> dict:
    policy = dict(DEFAULT_POLICY)
    policy.update(payload.get("policy", {}))
    competitors = payload.get("competitors")
    if not isinstance(competitors, list) or not competitors:
        return {"policy": policy, "competitors": []}
    rows = [evaluate_competitor(c, policy) for c in competitors]
    # Most signals moving (most corroborated read) first — attention should
    # go to the competitor with the richest evidence, not the loudest single number.
    rows.sort(key=lambda r: (len(r["patterns"]), r.get("signal_count", 0)), reverse=True)
    return {"policy": policy, "competitors": rows}


# ─────────────────────────── demo ───────────────────────────────────────────
DEMO_INPUT = {
    "competitors": [
        {
            # The skill's own worked example: price -11%, inventory proxy -34%,
            # rank improved 27 positions, review velocity 3.4x.
            "name": "Competitor X",
            "price": {"current": 890, "prior": 1000},
            "inventory_proxy": {"current": 66, "prior": 100},
            "rank": {"current": 23, "prior": 50},
            "reviews_gained": {"current": 34, "prior": 10},
        },
        {
            # Inventory down sharply, price steady, rank falling -> stockout risk.
            "name": "Competitor Y",
            "price": {"current": 1005, "prior": 1000},
            "inventory_proxy": {"current": 20, "prior": 90},
            "rank": {"current": 61, "prior": 40},
        },
        {
            # Only one signal available -> no inference attempted.
            "name": "Competitor Z",
            "price": {"current": 950, "prior": 1000},
        },
    ]
}


def demo() -> int:
    print("=" * 68)
    print("DEMO - competitor-monitor: worked example, a stockout risk, and one unscorable")
    print("=" * 68)
    report = evaluate(DEMO_INPUT)
    for row in report["competitors"]:
        print(f"\n> {row['competitor']}  ({len(row['patterns'])} pattern(s) matched)")
        for k, v in row["deltas"].items():
            print(f"  {k}: {v}")
        for m in row["patterns"]:
            print(f"  [{m['pattern']}] {m['reading']}")
            print(f"    -> {m['monitoring_posture']}")
        if not row["patterns"]:
            print(f"  pattern: {row['pattern']}" + (f"  ({row.get('note')})" if row.get("note") else ""))

    by_name = {r["competitor"]: r for r in report["competitors"]}
    x_patterns = {m["pattern"] for m in by_name["Competitor X"]["patterns"]}
    ok = (
        # Price fell 11% (not "flat"), so this reads as a genuine discount-led
        # clearance, not an ad-driven push without discounting — the two
        # patterns are mutually exclusive by construction on the price signal,
        # and a single blended narrative (discount + rank gain) is correct here.
        x_patterns == {"clearance_push"}
        and by_name["Competitor Y"]["pattern"] == "stockout_risk"
        and by_name["Competitor Z"]["pattern"] == "no_clear_pattern"
    )
    print("\n" + ("demo OK - worked example reads as a clearance push, "
                  "stockout risk caught, single-signal competitor refused a verdict"
                  if ok else "demo UNEXPECTED - check implementation"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Competitor signal pattern matcher")
    ap.add_argument("input", nargs="?", help="path to INPUT.json")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.input:
        ap.error("provide INPUT.json (or use --demo)")
    with open(args.input) as f:
        payload = json.load(f)
    report = evaluate(payload)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
