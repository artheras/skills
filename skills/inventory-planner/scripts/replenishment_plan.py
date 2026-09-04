#!/usr/bin/env python3
"""
replenishment_plan.py — per-SKU restock sizing: stock + velocity + lead time
-> a draft reorder quantity, or an honest refusal to size it.

Converts "how much should I reorder" into either a sized suggestion with a
disclosed status, or a refusal for any SKU whose inputs don't support one:

  classification : days_of_cover = current_stock / daily_sales_velocity,
                   compared against reorder_point_days = lead_time_days +
                   safety_stock_days, into stockout / urgent / reorder_now / ok
  refusal        : no daily_sales_velocity -> velocity_unavailable, no
                   lead_time_days -> lead_time_missing. Neither is ever
                   backfilled with a guessed number.
  sizing         : suggested_order_qty covers the reorder point plus a
                   review-period buffer, net of stock already in transit,
                   rounded up to a declared MOQ (rounding disclosed).
  authority      : every plan is `status: "draft"`. This script has no
                   concept of submitting a purchase order — that is a human
                   decision made in the supplier/ERP interface.

Exit 0 = plan produced (even if every SKU needs more data first — that's a
successful, honest run). Exit 1 = the input itself was invalid.

Input: a single JSON file (see references/inventory-schema.md):
  review_period_days?  skus[]: sku, current_stock, daily_sales_velocity?,
                        lead_time_days?, safety_stock_days?, on_order_qty?,
                        moq?, unit_cost?

Try it with no data:  python replenishment_plan.py --demo
The demo plans four SKUs: one healthy, one due for reorder, one urgent with
no safety margin left, and one with no sales history yet (refused, not guessed).

Stdlib only — runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

DEFAULT_SAFETY_STOCK_DAYS = 7.0
DEFAULT_REVIEW_PERIOD_DAYS = 14.0


def plan_sku(sku_input: dict, review_period_days: float) -> dict:
    sku = sku_input.get("sku")
    flags: list[str] = []

    current_stock = sku_input.get("current_stock")
    if not isinstance(current_stock, (int, float)):
        return {"sku": sku, "status": "invalid_input", "flags": ["missing_current_stock"],
                "suggested_order_qty": None}

    velocity = sku_input.get("daily_sales_velocity")
    if not isinstance(velocity, (int, float)) or velocity <= 0:
        return {"sku": sku, "status": "velocity_unavailable",
                "flags": ["no reorder quantity sized — not enough sales history to estimate velocity"],
                "current_stock": current_stock, "suggested_order_qty": None}

    lead_time = sku_input.get("lead_time_days")
    if not isinstance(lead_time, (int, float)) or lead_time <= 0:
        return {"sku": sku, "status": "lead_time_missing",
                "flags": ["no reorder point computed — supplier lead time not declared"],
                "current_stock": current_stock, "daily_sales_velocity": velocity,
                "suggested_order_qty": None}

    safety_days = sku_input.get("safety_stock_days", DEFAULT_SAFETY_STOCK_DAYS)
    if not isinstance(safety_days, (int, float)) or safety_days < 0:
        safety_days = DEFAULT_SAFETY_STOCK_DAYS
        flags.append("safety_stock_days invalid or missing — defaulted to "
                      f"{DEFAULT_SAFETY_STOCK_DAYS:g} days")

    on_order = sku_input.get("on_order_qty")
    if on_order is None:
        on_order = 0
        flags.append("on_order_unconfirmed — treated as 0; confirm no shipment is already in transit")
    elif not isinstance(on_order, (int, float)) or on_order < 0:
        on_order = 0
        flags.append("on_order_qty invalid — treated as 0")

    days_of_cover = current_stock / velocity
    reorder_point_days = lead_time + safety_days

    if days_of_cover <= 0:
        status = "stockout"
    elif days_of_cover < lead_time:
        status = "urgent"
    elif days_of_cover < reorder_point_days:
        status = "reorder_now"
    else:
        status = "ok"

    suggested_qty = 0
    rounded_to_moq = False
    if status in ("stockout", "urgent", "reorder_now"):
        target_cover_days = reorder_point_days + review_period_days
        needed_units = target_cover_days * velocity - current_stock - on_order
        suggested_qty = max(0, math.ceil(needed_units))
        moq = sku_input.get("moq")
        if isinstance(moq, (int, float)) and moq > 0 and 0 < suggested_qty < moq:
            suggested_qty = int(math.ceil(moq))
            rounded_to_moq = True

    result = {
        "sku": sku,
        "status": status,
        "days_of_cover": round(days_of_cover, 1),
        "reorder_point_days": round(reorder_point_days, 1),
        "current_stock": current_stock,
        "daily_sales_velocity": velocity,
        "on_order_qty": on_order,
        "suggested_order_qty": suggested_qty,
        "rounded_to_moq": rounded_to_moq,
        "flags": flags,
    }

    unit_cost = sku_input.get("unit_cost")
    if isinstance(unit_cost, (int, float)) and suggested_qty > 0:
        result["estimated_order_value"] = round(unit_cost * suggested_qty, 2)
        result["estimated_order_value_is_estimate"] = True

    return result


def plan(payload: dict) -> dict:
    review_period_days = payload.get("review_period_days", DEFAULT_REVIEW_PERIOD_DAYS)
    if not isinstance(review_period_days, (int, float)) or review_period_days < 0:
        review_period_days = DEFAULT_REVIEW_PERIOD_DAYS

    skus = payload.get("skus")
    if not isinstance(skus, list) or not skus:
        return {"status": "draft", "skus": [], "summary": {"error": "no skus provided"}}

    rows = [plan_sku(s, review_period_days) for s in skus]
    summary = {
        "stockout": sum(1 for r in rows if r["status"] == "stockout"),
        "urgent": sum(1 for r in rows if r["status"] == "urgent"),
        "reorder_now": sum(1 for r in rows if r["status"] == "reorder_now"),
        "ok": sum(1 for r in rows if r["status"] == "ok"),
        "needs_more_data": sum(1 for r in rows if r["status"] in ("velocity_unavailable", "lead_time_missing")),
    }
    return {"status": "draft", "skus": rows, "summary": summary}


# ─────────────────────────── demo ───────────────────────────────────────────
DEMO_INPUT = {
    "review_period_days": 14,
    "skus": [
        {"sku": "OZ-88213", "current_stock": 340, "daily_sales_velocity": 8.0,
         "lead_time_days": 18, "safety_stock_days": 7, "on_order_qty": 0},
        {"sku": "OZ-91004", "current_stock": 200, "daily_sales_velocity": 10.0,
         "lead_time_days": 18, "safety_stock_days": 7, "on_order_qty": 0, "moq": 200, "unit_cost": 3.4},
        {"sku": "OZ-77451", "current_stock": 40, "daily_sales_velocity": 6.0,
         "lead_time_days": 18, "safety_stock_days": 7, "on_order_qty": 0},
        {"sku": "OZ-NEW-01", "current_stock": 500, "daily_sales_velocity": None,
         "lead_time_days": 18},
    ],
}


def demo() -> int:
    print("=" * 68)
    print("DEMO - inventory-planner: healthy, due, urgent, and unsizeable SKUs")
    print("=" * 68)
    report = plan(DEMO_INPUT)
    for row in report["skus"]:
        print(f"\n> {row['sku']}  status={row['status']}")
        for k in ("days_of_cover", "reorder_point_days", "suggested_order_qty", "rounded_to_moq"):
            if k in row:
                print(f"  {k}: {row[k]}")
        for f in row.get("flags", []):
            print(f"  [flag] {f}")
    print(f"\nSummary: {report['summary']}")
    ok = (
        report["summary"]["ok"] == 1
        and report["summary"]["reorder_now"] == 1
        and report["summary"]["urgent"] == 1
        and report["summary"]["needs_more_data"] == 1
    )
    print("\n" + ("demo OK - one of each status, unsizeable SKU refused rather than guessed"
                  if ok else "demo UNEXPECTED - check implementation"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Replenishment plan sizer")
    ap.add_argument("input", nargs="?", help="path to INPUT.json")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.input:
        ap.error("provide INPUT.json (or use --demo)")
    with open(args.input) as f:
        payload = json.load(f)
    report = plan(payload)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
