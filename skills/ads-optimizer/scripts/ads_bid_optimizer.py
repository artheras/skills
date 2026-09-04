#!/usr/bin/env python3
"""
ads_bid_optimizer.py — raw campaign metrics + a declared ACOS policy ->
one ranked recommendation per campaign. Never a bid change.

Applies four rules, first match wins, to every campaign that has enough
spend to mean anything:

  insufficient_data     : spend < min_spend_for_signal -> not scored
  recommend_pause        : zero orders at meaningful spend -> not "a bit
                            inefficient", not working
  recommend_decrease_bid : acos > target_acos AND orders below the low-order
                            threshold -> step down, capped at max_step_pct
  recommend_increase_bid : acos comfortably under target AND the campaign is
                            budget-constrained -> step up, capped at
                            max_step_pct
  no_action               : inside the target band

Every recommendation carries the trigger rule and a plain-language reason —
"ACOS 48% > 35% target, orders below threshold" — not a bare instruction.
This script never calls an ads API; it has no side effects at all.

Input: a single JSON file (see references/ads-schema.md):
  policy{target_acos, min_spend_for_signal?, min_orders_low_threshold?,
         decrease_step_pct?, increase_step_pct?, max_step_pct?,
         scale_up_acos_margin?, budget_utilization_threshold?}
  campaigns[]: name, spend, ad_attributed_revenue, orders, daily_budget?

Try it with no data:  python ads_bid_optimizer.py --demo
The demo reproduces the skill's own worked example (spend 7,830, ACOS 48%
against a 35% target -> recommend -15%) plus a pause candidate, a
budget-constrained scale-up candidate, a healthy no-action campaign, and a
low-spend campaign refused for insufficient data.

Stdlib only — runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys

DEFAULT_POLICY = {
    "min_spend_for_signal": 5000,
    "min_orders_low_threshold": 2,
    "decrease_step_pct": 0.15,
    "increase_step_pct": 0.10,
    "max_step_pct": 0.25,
    "scale_up_acos_margin": 0.6,
    "budget_utilization_threshold": 0.9,
}


def _resolve_policy(policy_input: dict) -> dict:
    if "target_acos" not in policy_input:
        raise ValueError("policy.target_acos is required — this skill does not assume a target")
    resolved = dict(DEFAULT_POLICY)
    resolved.update(policy_input)
    return resolved


def evaluate_campaign(campaign: dict, policy: dict) -> dict:
    name = campaign.get("name", "unnamed")
    spend = campaign.get("spend", 0)
    revenue = campaign.get("ad_attributed_revenue", 0)
    orders = campaign.get("orders", 0)
    daily_budget = campaign.get("daily_budget")

    acos = (spend / revenue) if revenue > 0 else None

    if spend < policy["min_spend_for_signal"]:
        return {
            "campaign": name, "action": "insufficient_data", "spend": spend, "acos": acos,
            "reason": f"spend {spend:g} is below the {policy['min_spend_for_signal']:g} "
                      "minimum for a meaningful signal — not scored",
        }

    if orders == 0:
        return {
            "campaign": name, "action": "recommend_pause", "spend": spend, "acos": acos,
            "reason": f"spent {spend:g} with zero attributed orders — this isn't inefficient, "
                      "it isn't converting",
        }

    target = policy["target_acos"]
    max_step = policy["max_step_pct"]

    if acos is not None and acos > target and orders < policy["min_orders_low_threshold"]:
        step = min(policy["decrease_step_pct"], max_step)
        return {
            "campaign": name, "action": "recommend_decrease_bid", "spend": spend, "acos": acos,
            "adjustment_pct": -step,
            "reason": f"ACOS {acos:.0%} > {target:.0%} target with only {orders} order(s) "
                      f"(below the {policy['min_orders_low_threshold']}-order threshold) — "
                      f"reduce bid {step:.0%}",
        }

    if (
        acos is not None
        and acos < target * policy["scale_up_acos_margin"]
        and isinstance(daily_budget, (int, float))
        and daily_budget > 0
        and (spend / daily_budget) >= policy["budget_utilization_threshold"]
    ):
        step = min(policy["increase_step_pct"], max_step)
        return {
            "campaign": name, "action": "recommend_increase_bid", "spend": spend, "acos": acos,
            "adjustment_pct": step,
            "reason": f"ACOS {acos:.0%} is well under the {target:.0%} target and spend is at "
                      f"{spend / daily_budget:.0%} of daily budget — likely leaving orders on the "
                      f"table, raise bid {step:.0%}",
        }

    return {
        "campaign": name, "action": "no_action", "spend": spend, "acos": acos,
        "reason": "inside the target band, no rule fired",
    }


def evaluate(payload: dict) -> dict:
    policy = _resolve_policy(payload.get("policy", {}))
    campaigns = payload.get("campaigns")
    if not isinstance(campaigns, list) or not campaigns:
        return {"policy": policy, "recommendations": []}
    rows = [evaluate_campaign(c, policy) for c in campaigns]
    return {"policy": policy, "recommendations": rows}


# ─────────────────────────── demo ───────────────────────────────────────────
DEMO_INPUT = {
    "policy": {"target_acos": 0.35},
    "campaigns": [
        # The skill's own worked example: spend 7,830, ACOS 48%, target 35% -> -15%.
        {"name": "Campaign A - Kitchen Organizers", "spend": 7830, "ad_attributed_revenue": 16312.5, "orders": 1},
        # Zero orders at meaningful spend -> pause candidate, not a bid trim.
        {"name": "Campaign B - Seasonal Decor", "spend": 6200, "ad_attributed_revenue": 0, "orders": 0},
        # Efficient ACOS, pinned against its daily budget -> scale-up candidate.
        {"name": "Campaign C - Bestseller Mugs", "spend": 5400, "ad_attributed_revenue": 27000,
         "orders": 45, "daily_budget": 5500},
        # Healthy and not budget-constrained -> no action.
        {"name": "Campaign D - Steady Kitchenware", "spend": 9000, "ad_attributed_revenue": 30000,
         "orders": 25, "daily_budget": 20000},
        # Not enough spend yet to mean anything -> refused, not guessed.
        {"name": "Campaign E - New Launch", "spend": 300, "ad_attributed_revenue": 900, "orders": 1},
    ],
}


def demo() -> int:
    print("=" * 68)
    print("DEMO - ads-optimizer: the skill's own worked example, plus three more rules")
    print("=" * 68)
    report = evaluate(DEMO_INPUT)
    for row in report["recommendations"]:
        print(f"\n> {row['campaign']}")
        print(f"  action: {row['action']}")
        if row.get("acos") is not None:
            print(f"  spend={row['spend']:g}  acos={row['acos']:.0%}")
        if "adjustment_pct" in row:
            print(f"  adjustment: {row['adjustment_pct']:+.0%}")
        print(f"  reason: {row['reason']}")

    by_name = {r["campaign"]: r for r in report["recommendations"]}
    ok = (
        by_name["Campaign A - Kitchen Organizers"]["action"] == "recommend_decrease_bid"
        and by_name["Campaign A - Kitchen Organizers"]["adjustment_pct"] == -0.15
        and by_name["Campaign B - Seasonal Decor"]["action"] == "recommend_pause"
        and by_name["Campaign C - Bestseller Mugs"]["action"] == "recommend_increase_bid"
        and by_name["Campaign D - Steady Kitchenware"]["action"] == "no_action"
        and by_name["Campaign E - New Launch"]["action"] == "insufficient_data"
    )
    print("\n" + ("demo OK - all five rule branches fired correctly, none executed anything"
                  if ok else "demo UNEXPECTED - check implementation"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ads bid recommendation engine")
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
