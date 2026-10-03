#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
carrier_scorecard.py — carrier ranking, freight anomalies and savings by lane, for a 3PL shipper.

Standard library only.

Ranking: within each lane, by the Wilson lower bound of the on-time rate, then
median cost/kg. A raw percentage puts 1/1 on time above 98/100; the lower bound
(0.21 vs 0.93) does not. Carrier-lanes with fewer than --min-shipments are
reported but not ranked.

Anomalies: cost/kg modified z-score > 3.5 within a lane,
    Mᵢ = 0.6745·(xᵢ − median)/MAD, or (xᵢ − median)/(1.253314·MeanAD) when MAD = 0.
The fallback matters: on a contracted lane most shipments share one rate, MAD is
0, and that is exactly where an overcharge is plainest. Also billed weight
> 1.2 × actual weight.

Savings: only where an alternative carrier on the same lane is both cheaper per
kg and at least as reliable by the same lower bound, with enough shipments on
both sides. Estimate = volume × rate difference; contract terms, surcharges,
minimums and capacity are not modelled.

Shipper isolation as in inventory_policy.py: mixed shippers are refused unless
--owner or --all-owners is given, and refusals never name other shippers.

Same rules as Aria Code's `score_carriers` tool; --demo checks the same
hand-computed values.

Usage:
    python carrier_scorecard.py --waybills waybills.csv --owner ACME
    python carrier_scorecard.py --demo
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from statistics import NormalDist

THRESHOLD = 3.5
OVERBILLED = 1.2
MIN_LANE_ROWS = 5
INTERNAL = "INTERNAL — cross-shipper view; not for client distribution"


class InputError(ValueError):
    pass


def wilson_lower_bound(k: int, n: int, confidence: float = 0.95) -> float | None:
    if n <= 0:
        return None
    z = NormalDist().inv_cdf(1 - (1 - confidence) / 2)
    p = k / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def _num(rec, field, row, required=False):
    value = rec.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise InputError(f"Row {row}: {field} is required")
        return None
    if isinstance(value, bool):
        raise InputError(f"Row {row}: {field} must be a number")
    try:
        out = float(value)
    except (TypeError, ValueError):
        raise InputError(f"Row {row}: {field} must be a number") from None
    if not math.isfinite(out) or out < 0:
        raise InputError(f"Row {row}: {field} must be finite and non-negative")
    return out


def _flag(rec, field, row):
    value = rec.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "y", "1", "是"}:
        return True
    if text in {"false", "no", "n", "0", "否"}:
        return False
    raise InputError(f"Row {row}: {field} must be true/false")


def scope(records, owner=None, all_owners=False):
    labelled = [r for r in records if str(r.get("owner_id") or "").strip()]
    if not labelled:
        if owner:
            raise InputError(f"owner {owner!r} requested, but the records carry no owner_id")
        return records, {"mode": "single_tenant", "client_facing": True}
    if len(labelled) != len(records):
        raise InputError("some records have no owner_id and cannot be attributed to a shipper")
    owners = {str(r["owner_id"]).strip() for r in labelled}
    if owner:
        picked = [r for r in labelled if str(r["owner_id"]).strip() == owner]
        if not picked:
            raise InputError(f"No records for owner {owner!r}")
        return picked, {"mode": "single_owner", "owner_id": owner, "client_facing": True}
    if len(owners) == 1:
        return labelled, {"mode": "single_owner", "owner_id": next(iter(owners)), "client_facing": True}
    if all_owners:
        return labelled, {"mode": "all_owners", "shipper_count": len(owners), "client_facing": False, "marker": INTERNAL}
    raise InputError(f"These records belong to {len(owners)} different shippers. "
                     f"Pass --owner for one shipper, or --all-owners for the internal view.")


def score(records, owner=None, all_owners=False, min_shipments=20, confidence=0.95):
    if not records:
        raise InputError("No waybill records supplied")
    records, scope_info = scope(records, owner, all_owners)
    cells = defaultdict(lambda: {"n": 0, "cost": 0.0, "kg": 0.0, "rates": [], "ot_n": 0, "ot": 0, "ex_n": 0, "ex": 0})
    lane_rates = defaultdict(list)
    anomalies = []
    for row, rec in enumerate(records, 1):
        carrier = str(rec.get("carrier") or "").strip()
        if not carrier:
            raise InputError(f"Row {row}: carrier is required")
        cost = _num(rec, "total_cost", row, required=True)
        billed, actual = _num(rec, "billed_weight_kg", row), _num(rec, "actual_weight_kg", row)
        on_time, exception = _flag(rec, "is_on_time", row), _flag(rec, "has_exception", row)
        o, d = str(rec.get("origin") or "").strip(), str(rec.get("destination") or "").strip()
        lane = f"{o}→{d}" if o and d else "(all lanes)"
        waybill = str(rec.get("waybill_no") or f"row {row}")
        cell = cells[(lane, carrier)]
        cell["n"] += 1
        cell["cost"] += cost
        weight = billed or actual
        if weight:
            cell["kg"] += weight
            cell["rates"].append(cost / weight)
            lane_rates[lane].append((cost / weight, waybill, carrier))
        if on_time is not None:
            cell["ot_n"] += 1
            cell["ot"] += int(on_time)
        if exception is not None:
            cell["ex_n"] += 1
            cell["ex"] += int(exception)
        if actual and billed and billed > actual * OVERBILLED:
            anomalies.append({"waybill_no": waybill, "carrier": carrier, "lane": lane, "kind": "billed_weight",
                              "detail": f"billed {billed:g} kg vs actual {actual:g} kg"})

    for lane, rows in lane_rates.items():
        if len(rows) < MIN_LANE_ROWS:
            continue
        rates = [r for r, _, _ in rows]
        median = statistics.median(rates)
        deviations = [abs(r - median) for r in rates]
        mad = statistics.median(deviations)
        if mad > 0:
            scale = mad / 0.6745
        else:
            mean_ad = statistics.fmean(deviations)
            if mean_ad == 0:
                continue
            scale = 1.253314 * mean_ad
        for rate, waybill, carrier in rows:
            m = (rate - median) / scale
            if m > THRESHOLD:
                anomalies.append({"waybill_no": waybill, "carrier": carrier, "lane": lane, "kind": "cost_per_kg",
                                  "detail": f"{rate:.2f}/kg vs lane median {median:.2f}/kg (modified z {m:.1f})"})

    board = []
    for (lane, carrier), c in cells.items():
        lower = wilson_lower_bound(c["ot"], c["ot_n"], confidence)
        board.append({
            "lane": lane, "carrier": carrier, "shipments": c["n"],
            "on_time_rate": round(c["ot"] / c["ot_n"], 4) if c["ot_n"] else None,
            "on_time_lower_bound": round(lower, 4) if lower is not None else None,
            "median_cost_per_kg": round(statistics.median(c["rates"]), 4) if c["rates"] else None,
            "total_cost": round(c["cost"], 2), "total_kg": round(c["kg"], 2),
            "exception_rate": round(c["ex"] / c["ex_n"], 4) if c["ex_n"] else None,
            "rankable": c["n"] >= min_shipments and lower is not None, "rank_in_lane": None,
        })
    for lane in {b["lane"] for b in board}:
        ranked = sorted((b for b in board if b["lane"] == lane and b["rankable"]),
                        key=lambda b: (-b["on_time_lower_bound"],
                                       b["median_cost_per_kg"] if b["median_cost_per_kg"] is not None else math.inf,
                                       b["carrier"]))
        for i, b in enumerate(ranked, 1):
            b["rank_in_lane"] = i

    best = {}
    for lane in {b["lane"] for b in board}:
        eligible = [b for b in board if b["lane"] == lane and b["rankable"]
                    and b["median_cost_per_kg"] is not None and b["total_kg"] > 0]
        for cur in eligible:
            for alt in eligible:
                if alt is cur or alt["median_cost_per_kg"] >= cur["median_cost_per_kg"]:
                    continue
                if alt["on_time_lower_bound"] < cur["on_time_lower_bound"]:
                    continue
                est = round(cur["total_kg"] * (cur["median_cost_per_kg"] - alt["median_cost_per_kg"]), 2)
                key = (lane, cur["carrier"])
                if key not in best or est > best[key]["estimated_saving"]:
                    best[key] = {"lane": lane, "from_carrier": cur["carrier"], "to_carrier": alt["carrier"],
                                 "volume_kg": cur["total_kg"], "estimated_saving": est}
    savings = sorted(best.values(), key=lambda s: -s["estimated_saving"])
    board.sort(key=lambda b: (b["lane"], b["rank_in_lane"] or math.inf, b["carrier"]))
    assumptions = [
        f"ranked within lane by the {confidence:.0%} Wilson lower bound of on-time rate, then median cost/kg; "
        f"≥ {min_shipments} shipments to rank",
        f"cost/kg anomaly: modified z > {THRESHOLD} (MAD; 1.253314·MeanAD when MAD = 0); billed > {OVERBILLED:g}× actual weight",
        "savings: alternative must be cheaper per kg and at least as reliable; volume × rate difference, "
        "excluding contract terms, surcharges, minimums and capacity",
    ]
    if not scope_info["client_facing"]:
        assumptions.insert(0, INTERNAL)
    return {"scope": scope_info, "scorecard": board, "anomalies": anomalies, "savings": savings,
            "assumptions": assumptions}


def _waybills(carrier, n, on_time, cost_per_kg, kg=10.0):
    return [{"carrier": carrier, "origin": "SH", "destination": "BJ", "total_cost": cost_per_kg * kg,
             "billed_weight_kg": kg, "is_on_time": i < on_time, "waybill_no": f"{carrier}-{i}"} for i in range(n)]


def load(path: Path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("waybills") if isinstance(data, dict) else data
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def demo() -> int:
    """Hand-computed reference values:
      Wilson lower bound 1/1 = 1/(1+1.96²) = 0.2065; 98/100 = 0.9300.
      PRICEY 30×10 kg at 8/kg, 27/30 on time; CHEAP 30 at 5/kg, 29/30 → saving 300·(8−5) = 900.
      Contracted lane: seven at 5/kg, one 5.2, one 4.8, one 30 → only the 30/kg waybill is flagged.
    """
    failures = []
    if round(wilson_lower_bound(1, 1), 4) != 0.2065 or round(wilson_lower_bound(98, 100), 4) != 0.93:
        failures.append("Wilson lower bound")
    result = score(_waybills("PRICEY", 30, 27, 8.0) + _waybills("CHEAP", 30, 29, 5.0))
    if [(s["from_carrier"], s["to_carrier"], s["estimated_saving"]) for s in result["savings"]] != [("PRICEY", "CHEAP", 900.0)]:
        failures.append("savings")
    lane = _waybills("X", 9, 9, 5.0)
    lane[0]["total_cost"], lane[1]["total_cost"] = 52.0, 48.0
    lane.append({"carrier": "X", "origin": "SH", "destination": "BJ", "total_cost": 300, "billed_weight_kg": 10,
                 "waybill_no": "OUTLIER"})
    flagged = [a["waybill_no"] for a in score(lane)["anomalies"] if a["kind"] == "cost_per_kg"]
    if flagged != ["OUTLIER"]:
        failures.append(f"contracted-lane outlier (flagged {flagged})")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        print("DEMO MISMATCH: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("demo: reference values verified", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="3PL carrier scorecard")
    ap.add_argument("--waybills", type=Path, help="CSV or JSON of waybills")
    ap.add_argument("--owner", help="shipper (owner_id) to analyse")
    ap.add_argument("--all-owners", action="store_true", help="internal cross-shipper view")
    ap.add_argument("--min-shipments", type=int, default=20)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.waybills:
        ap.error("--waybills is required (or use --demo)")
    try:
        result = score(load(args.waybills) or [], args.owner, args.all_owners, args.min_shipments)
    except (InputError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
