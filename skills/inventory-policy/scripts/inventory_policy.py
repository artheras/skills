#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
inventory_policy.py — reorder points, safety stock and dead stock for a 3PL shipper.

Standard library only, so it runs anywhere an agent can run Python.

    z            = Φ⁻¹(service level)
    safety stock = z · √(L·σ_d² + d̄²·σ_L²)
    reorder point= d̄·L + safety stock
    order-up-to  = reorder point + d̄·R
    order qty    = order-up-to − (on hand + on order − backordered), when that position ≤ reorder point

ABC by annual consumption value within each shipper (80/95), XYZ by demand CV
(0.5/1.0), slow ≥ 30 days idle, dead ≥ 90. A SKU with under 14 days of demand
history gets no policy: it is reported as insufficient history.

Shipper isolation: records spanning several owner_id values are refused unless
--owner names one, or --all-owners asks for the internal cross-shipper view
(marked not for client distribution). Refusals never name other shippers.

Same formulas, thresholds and isolation rules as Aria Code's
`plan_inventory_policy` tool; --demo checks the same hand-computed values.

Usage:
    python inventory_policy.py --skus skus.csv --owner ACME
    python inventory_policy.py --demo
Exit 1 on unusable input.
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

MIN_HISTORY = 14
SLOW_DAYS, DEAD_DAYS, EXCESS_COVER = 30.0, 90.0, 180.0
ABC = (0.80, 0.95)
XYZ = (0.5, 1.0)
INTERNAL = "INTERNAL — cross-shipper view; not for client distribution"


class InputError(ValueError):
    pass


def _num(rec, field, row, required=False, positive=False):
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
    if not math.isfinite(out) or out < 0 or (positive and out == 0):
        raise InputError(f"Row {row}: {field} must be finite and {'positive' if positive else 'non-negative'}")
    return out


def _series(rec, field, row):
    value = rec.get(field)
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    parts = value if isinstance(value, list) else [p for p in str(value).replace(",", ";").split(";") if p.strip()]
    out = []
    for i, part in enumerate(parts, 1):
        try:
            item = float(part)
        except (TypeError, ValueError):
            raise InputError(f"Row {row}: {field} item {i} must be a number") from None
        if not math.isfinite(item) or item < 0:
            raise InputError(f"Row {row}: {field} item {i} must be non-negative")
        out.append(item)
    return out


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


def plan(records, owner=None, all_owners=False, service_level=0.95, review_days=7.0):
    if not records:
        raise InputError("No SKU records supplied")
    if not 0.5 <= service_level < 1:
        raise InputError("service level must be at least 0.5 and below 1")
    records, scope_info = scope(records, owner, all_owners)
    z = NormalDist().inv_cdf(service_level)
    items = []
    for row, rec in enumerate(records, 1):
        sku = str(rec.get("sku") or "").strip()
        if not sku:
            raise InputError(f"Row {row}: sku is required")
        on_hand = _num(rec, "on_hand", row, required=True)
        position = on_hand + (_num(rec, "on_order", row) or 0) - (_num(rec, "backorder", row) or 0)
        lead = _num(rec, "lead_time_days", row, required=True, positive=True)
        lead_std = _num(rec, "lead_time_std_days", row) or 0.0
        unit_cost = _num(rec, "unit_cost", row)
        idle = _num(rec, "days_since_last_movement", row)
        history = _series(rec, "daily_demand", row)
        if history is None:
            raise InputError(f"Row {row}: daily_demand is required")
        mean = statistics.fmean(history) if history else 0.0
        std = statistics.stdev(history) if len(history) >= 2 else 0.0
        item = {
            "owner_id": str(rec.get("owner_id") or "").strip() or None, "sku": sku,
            "on_hand": on_hand, "inventory_position": round(position, 2),
            "avg_daily_demand": round(mean, 4), "demand_std": round(std, 4), "history_days": len(history),
            "safety_stock": None, "reorder_point": None, "order_up_to": None, "suggested_order_qty": 0,
            "days_of_cover": round(on_hand / mean, 1) if mean > 0 else None,
            "abc": None, "xyz": None, "movement": None, "flags": [],
            "annual_value": round(mean * 365 * unit_cost, 2) if unit_cost is not None else None,
        }
        if mean > 0:
            cv = std / mean
            item["xyz"] = "X" if cv <= XYZ[0] else "Y" if cv <= XYZ[1] else "Z"
        if idle is not None:
            item["movement"] = "dead" if idle >= DEAD_DAYS else "slow" if idle >= SLOW_DAYS else "active"
        if mean == 0:
            item["action"] = "no_demand"
        elif len(history) < MIN_HISTORY:
            item["action"] = "insufficient_history"
            item["flags"].append(f"{len(history)} days of history; {MIN_HISTORY} needed")
        else:
            safety = z * math.sqrt(lead * std ** 2 + mean ** 2 * lead_std ** 2)
            rop = mean * lead + safety
            up_to = rop + mean * review_days
            item.update(safety_stock=math.ceil(safety), reorder_point=math.ceil(rop), order_up_to=math.ceil(up_to))
            if position <= rop:
                item["action"] = "reorder"
                item["suggested_order_qty"] = max(0, math.ceil(up_to - position))
            else:
                item["action"] = "ok"
        if item["days_of_cover"] is not None and item["days_of_cover"] > EXCESS_COVER:
            item["flags"].append(f"{item['days_of_cover']:g} days of cover")
        items.append(item)

    groups = defaultdict(list)
    for item in items:
        if item["annual_value"] is not None:
            groups[item["owner_id"] or ""].append(item)
    for group in groups.values():
        total = sum(i["annual_value"] for i in group)
        cumulative = 0.0
        for item in sorted(group, key=lambda i: (-i["annual_value"], i["sku"])):
            if total > 0:
                share = cumulative / total
                item["abc"] = "A" if share < ABC[0] else "B" if share < ABC[1] else "C"
            cumulative += item["annual_value"]

    assumptions = [
        f"service level {service_level:.1%} → z = {z:.3f}",
        "safety stock = z·√(L·σ_d² + d̄²·σ_L²); reorder point = d̄·L + safety stock",
        f"order-up-to = reorder point + d̄·{review_days:g}; quantities rounded up to whole units",
        f"no policy below {MIN_HISTORY} days of demand history",
        "capacity, MOQs, case packs and supplier terms are not modelled",
    ]
    if not scope_info["client_facing"]:
        assumptions.insert(0, INTERNAL)
    return {"scope": scope_info, "items": items, "assumptions": assumptions}


def load(path: Path):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("skus") if isinstance(data, dict) else data
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def demo() -> int:
    """Hand-computed reference: d̄ = 15, σ_d = √(350/13), L = 4, 95% → SS 18, ROP 78, S 183, qty 133."""
    result = plan([{"sku": "A", "on_hand": 50, "lead_time_days": 4,
                    "daily_demand": [10] * 7 + [20] * 7}])
    a = result["items"][0]
    expected = {"safety_stock": 18, "reorder_point": 78, "order_up_to": 183, "suggested_order_qty": 133}
    got = {k: a[k] for k in expected}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if got != expected:
        print(f"DEMO MISMATCH: expected {expected}, got {got}", file=sys.stderr)
        return 1
    try:
        plan([{"owner_id": "ACME", "sku": "A", "on_hand": 1, "lead_time_days": 1, "daily_demand": [1] * 14},
              {"owner_id": "OTHER", "sku": "B", "on_hand": 1, "lead_time_days": 1, "daily_demand": [1] * 14}])
    except InputError as exc:
        if "OTHER" in str(exc):
            print("DEMO FAILURE: a refusal named another shipper", file=sys.stderr)
            return 1
    else:
        print("DEMO FAILURE: mixed shippers were not refused", file=sys.stderr)
        return 1
    print("demo: reference values and shipper isolation verified", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="3PL inventory policy")
    ap.add_argument("--skus", type=Path, help="CSV or JSON of SKU records")
    ap.add_argument("--owner", help="shipper (owner_id) to analyse")
    ap.add_argument("--all-owners", action="store_true", help="internal cross-shipper view")
    ap.add_argument("--service-level", type=float, default=0.95)
    ap.add_argument("--review-days", type=float, default=7.0)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.skus:
        ap.error("--skus is required (or use --demo)")
    try:
        result = plan(load(args.skus) or [], args.owner, args.all_owners, args.service_level, args.review_days)
    except (InputError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
