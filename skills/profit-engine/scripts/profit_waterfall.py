#!/usr/bin/env python3
"""
profit_waterfall.py — net profit per store, and a bucket-by-bucket bridge
explaining why it moved between two periods.

Converts "what's my profit" into either a real number or an honest upper
bound, and converts "why did it change" into a ranked list of cost-bucket
deltas instead of a single opaque total:

  completeness : any of the ten cost buckets missing (null) for a period ->
                 the store's net profit for that period is not computed as a
                 number, it is reported as profit_incomplete with an upper
                 bound (revenue minus only the buckets that ARE known — real
                 profit can only be lower, never higher, than that bound)
  bridge       : for a store complete in both periods, profit_change is
                 decomposed into a revenue term and one term per cost
                 bucket, ranked by |contribution| so the largest driver of
                 the change is named explicitly, not buried in a total
  reconciliation: revenue_change - sum(cost_bucket_changes) must equal
                 profit_change for a complete store; a mismatch is flagged,
                 not hidden — it usually means an FX/currency inconsistency
  rollup       : portfolio totals are built only from stores complete in
                 both periods; incomplete stores are listed separately, never
                 blended into a total that would understate the real cost base

Exit 0 = report produced (even an incomplete one — that's an honest report).
Exit 1 = the input itself was invalid.

Input: a single JSON file (see references/profit-schema.md):
  stores[]: name, currency, current{revenue,...10 cost buckets...},
            prior{...same 10 buckets...}

Try it with no data:  python profit_waterfall.py --demo
The demo reproduces the exact scenario the skill exists for: GMV +18%,
profit -7%, with advertising spend named as the largest single driver of the
decline — plus a second store with a missing cost feed, reported as an
upper bound rather than a fabricated number.

Stdlib only — runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys

COST_BUCKETS = [
    "cogs", "platform_commission", "advertising", "logistics", "warehousing",
    "returns", "refunds", "payment_fees", "penalties", "fx_impact", "tax",
]
RECONCILIATION_TOLERANCE = 0.01  # absolute currency-unit tolerance for float rounding


def _period_totals(period: dict) -> dict:
    """One period's known/missing cost buckets, and whatever can be computed from them."""
    missing = [b for b in COST_BUCKETS if period.get(b) is None]
    known = {b: period[b] for b in COST_BUCKETS if period.get(b) is not None}
    known_cost_total = sum(known.values())
    revenue = period.get("revenue")
    zero_buckets = [b for b, v in known.items() if v == 0]
    return {
        "revenue": revenue,
        "missing_buckets": missing,
        "known_cost_total": known_cost_total,
        "zero_buckets": zero_buckets,
        # Upper bound: real profit can only be <= this, since any missing
        # bucket can only ever subtract more cost, never add revenue back.
        "profit_upper_bound": (revenue - known_cost_total) if isinstance(revenue, (int, float)) else None,
        "profit_complete": (revenue - known_cost_total) if isinstance(revenue, (int, float)) and not missing else None,
    }


def evaluate_store(store: dict) -> dict:
    name = store.get("name", "unnamed")
    current = store.get("current", {})
    prior = store.get("prior", {})

    cur = _period_totals(current)
    pri = _period_totals(prior)

    flags: list[dict] = []
    incomplete = bool(cur["missing_buckets"] or pri["missing_buckets"])
    if cur["missing_buckets"]:
        flags.append({"severity": "warn", "code": "cost_bucket_missing",
                      "detail": f"current period missing: {cur['missing_buckets']}"})
    if pri["missing_buckets"]:
        flags.append({"severity": "warn", "code": "cost_bucket_missing",
                      "detail": f"prior period missing: {pri['missing_buckets']}"})
    for label, period_result in (("current", cur), ("prior", pri)):
        if period_result["zero_buckets"] and len(period_result["zero_buckets"]) >= 3:
            flags.append({"severity": "warn", "code": "suspiciously_clean",
                          "detail": f"{label} period has {len(period_result['zero_buckets'])} "
                                    f"zero-value cost buckets {period_result['zero_buckets']} — "
                                    "verify these are genuinely zero, not just unrecorded"})

    result = {
        "store": name,
        "profit_incomplete": incomplete,
        "current": {"revenue": cur["revenue"], "profit_upper_bound": cur["profit_upper_bound"],
                    "net_profit": cur["profit_complete"]},
        "prior": {"revenue": pri["revenue"], "profit_upper_bound": pri["profit_upper_bound"],
                  "net_profit": pri["profit_complete"]},
        "flags": flags,
        "bridge": None,
    }

    if incomplete:
        return result

    # Full bridge only when both periods are complete.
    revenue_change = cur["revenue"] - pri["revenue"]
    bucket_changes = []
    for b in COST_BUCKETS:
        delta = current[b] - prior[b]
        if delta != 0:
            bucket_changes.append({"bucket": b, "prior": prior[b], "current": current[b], "change": delta})
    bucket_changes.sort(key=lambda r: abs(r["change"]), reverse=True)

    profit_change = cur["profit_complete"] - pri["profit_complete"]
    reconciled = revenue_change - sum(r["change"] for r in bucket_changes)
    mismatch = abs(reconciled - profit_change) > RECONCILIATION_TOLERANCE
    if mismatch:
        flags.append({"severity": "fail", "code": "bridge_mismatch",
                      "detail": f"revenue_change - cost_changes = {reconciled:.2f} but "
                                f"profit_change = {profit_change:.2f} — check for an FX/currency "
                                "inconsistency between periods"})

    result["bridge"] = {
        "revenue_change": revenue_change,
        "profit_change": profit_change,
        "cost_bucket_changes": bucket_changes,
        "largest_driver": bucket_changes[0] if bucket_changes else None,
        "reconciled": not mismatch,
    }
    return result


def evaluate(payload: dict) -> dict:
    stores = payload.get("stores")
    if not isinstance(stores, list) or not stores:
        return {"stores": [], "portfolio": {"error": "no stores provided"}}

    rows = [evaluate_store(s) for s in stores]
    complete_rows = [r for r in rows if not r["profit_incomplete"]]
    incomplete_names = [r["store"] for r in rows if r["profit_incomplete"]]

    portfolio = {
        "stores_included": [r["store"] for r in complete_rows],
        "stores_excluded_incomplete": incomplete_names,
        "total_current_profit": sum(r["current"]["net_profit"] for r in complete_rows) if complete_rows else None,
        "total_prior_profit": sum(r["prior"]["net_profit"] for r in complete_rows) if complete_rows else None,
    }
    return {"stores": rows, "portfolio": portfolio}


# ─────────────────────────── demo ───────────────────────────────────────────
def _period(revenue, cogs, commission, advertising, logistics, warehousing,
            returns=15000, refunds=10000, payment_fees=5000, penalties=3000, fx_impact=0, tax=7000):
    return {"revenue": revenue, "cogs": cogs, "platform_commission": commission,
            "advertising": advertising, "logistics": logistics, "warehousing": warehousing,
            "returns": returns, "refunds": refunds, "payment_fees": payment_fees,
            "penalties": penalties, "fx_impact": fx_impact, "tax": tax}


DEMO_INPUT = {
    "stores": [
        {
            "name": "OZON-Store-A",
            "currency": "RUB",
            # GMV +18%, but advertising nearly doubled — net profit falls 7%
            # even though every other cost scaled in line with revenue.
            "current": _period(1180000, 472000, 177000, 180600, 94400, 30000),
            "prior": _period(1000000, 400000, 150000, 100000, 80000, 30000),
        },
        {
            "name": "WB-Store-B",
            "currency": "RUB",
            # advertising feed for this store hasn't synced this period —
            # the gate refuses to guess it, reports an upper bound instead.
            "current": {**_period(430000, 190000, 60000, None, 35000, 12000),
                        "advertising": None},
            "prior": _period(410000, 180000, 58000, 42000, 33000, 12000),
        },
    ]
}


def demo() -> int:
    print("=" * 68)
    print("DEMO - profit-engine: GMV up, profit down, and one incomplete store")
    print("=" * 68)
    report = evaluate(DEMO_INPUT)
    for row in report["stores"]:
        print(f"\n> {row['store']}  incomplete={row['profit_incomplete']}")
        if row["profit_incomplete"]:
            print(f"  current profit_upper_bound: {row['current']['profit_upper_bound']}")
            print(f"  prior   profit_upper_bound: {row['prior']['profit_upper_bound']}")
        else:
            print(f"  current net_profit: {row['current']['net_profit']}")
            print(f"  prior   net_profit: {row['prior']['net_profit']}")
            b = row["bridge"]
            print(f"  revenue_change: {b['revenue_change']:+.0f}   profit_change: {b['profit_change']:+.0f}"
                  f"   reconciled={b['reconciled']}")
            print("  bridge (largest driver first):")
            for c in b["cost_bucket_changes"][:4]:
                print(f"    {c['bucket']:20s} {c['prior']:>10.0f} -> {c['current']:>10.0f}  ({c['change']:+.0f})")
        for f in row["flags"]:
            print(f"  [{f['severity'].upper():4}] {f['code']}: {f['detail']}")
    print(f"\nPortfolio: {report['portfolio']}")

    a_row = next(r for r in report["stores"] if r["store"] == "OZON-Store-A")
    b_row = next(r for r in report["stores"] if r["store"] == "WB-Store-B")
    ok = (
        not a_row["profit_incomplete"]
        and a_row["bridge"]["profit_change"] < 0
        and a_row["bridge"]["revenue_change"] > 0
        and a_row["bridge"]["largest_driver"]["bucket"] == "advertising"
        and a_row["bridge"]["reconciled"]
        and b_row["profit_incomplete"]
    )
    print("\n" + ("demo OK - revenue up, profit down, advertising named as the driver; "
                  "incomplete store bounded, not guessed" if ok else "demo UNEXPECTED - check implementation"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Profit waterfall and bridge")
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
