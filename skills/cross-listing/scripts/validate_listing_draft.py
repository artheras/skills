#!/usr/bin/env python3
"""
validate_listing_draft.py — the completion gate for a cross-marketplace
listing migration draft.

A migrated listing that "looks done" and one that is actually safe to hand to
a seller for review differ in exactly the ways a human reviewer would miss on
a quick skim: an unmapped category quietly filed under the nearest guess, a
dimension the source never stated backfilled with a plausible number, a price
bumped 40% with no sign anyone meant to do that. This validator enforces the
draft contract described in `references/listing-schema.md` BEFORE the draft
is handed back to the seller:

  linkage    : source_platform/destination_platform/source_sku/internal_id
               all present — losing the link back to the source listing is
               treated the same as losing the listing
  publish    : `status` must be "draft" or "pending_review" — anything else
               (e.g. "published", "live") fails outright, mirroring
               execution-position's paper_only refusal
  category   : destination_id must be present — no match is a FAIL, never a
               best-guess category
  attributes : title, description, and at least one image are required
  honesty    : dimensions_source must be "declared" or "unknown", never a
               free-text excuse for a fabricated number; a shorter image list
               than the source needs images_omitted_reason; a price move
               beyond +/-15% needs price_change_confirmed=true

Exit 0 = draft is fit to hand to the seller (PASS or WARN). Exit 1 = fix the
draft first.

Usage:
  python validate_listing_draft.py DRAFT.json
  python validate_listing_draft.py --demo     # a clean draft and a broken one

Stdlib only — runs anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys

ALLOWED_STATUS = {"draft", "pending_review"}
DIMENSIONS_SOURCE_VALUES = {"declared", "unknown"}
PRICE_DELTA_CONFIRM_THRESHOLD = 0.15

REQUIRED_TOP_LEVEL = {
    "source_platform": str,
    "destination_platform": str,
    "source_sku": str,
    "internal_id": str,
    "status": str,
    "title": str,
    "description": str,
    "category": dict,
    "images": list,
    "price": dict,
}


def validate(draft: dict) -> dict:
    flags: list[dict] = []

    def flag(sev: str, code: str, detail: str):
        flags.append({"severity": sev, "code": code, "detail": detail})

    # structure / linkage
    for key, typ in REQUIRED_TOP_LEVEL.items():
        if key not in draft:
            flag("fail", "missing_field", f"required field `{key}` is absent")
        elif not isinstance(draft[key], typ):
            flag("fail", "wrong_type", f"`{key}` should be {typ.__name__}")
    if any(f["code"] in ("missing_field", "wrong_type") for f in flags):
        return _verdict(flags)

    for key in ("source_sku", "internal_id"):
        if not str(draft.get(key, "")).strip():
            flag("fail", "linkage_lost", f"`{key}` is empty — draft cannot be traced back to its source listing")

    # publish gate
    status = draft.get("status")
    if status not in ALLOWED_STATUS:
        flag("fail", "publish_not_allowed",
             f"status `{status}` is not one of {sorted(ALLOWED_STATUS)} — "
             "this skill only ever produces a draft, never a publish")

    # category
    category = draft.get("category", {})
    if not str(category.get("destination_id") or "").strip():
        flag("fail", "unmapped_category",
             "category.destination_id is missing — do not file under a guessed category")

    # required content
    if not str(draft.get("title", "")).strip():
        flag("fail", "empty_title", "title is empty")
    if not str(draft.get("description", "")).strip():
        flag("fail", "empty_description", "description is empty")

    images = draft.get("images") or []
    if not images:
        flag("fail", "no_images", "images list is empty")
    source_image_count = draft.get("source_image_count")
    if isinstance(source_image_count, int) and len(images) < source_image_count:
        reason = draft.get("images_omitted_reason")
        if not str(reason or "").strip():
            flag("fail", "undisclosed_image_drop",
                 f"draft has {len(images)} image(s), source had {source_image_count}, "
                 "and images_omitted_reason is not set")

    # dimensions / weight honesty
    dims_source = draft.get("dimensions_source")
    if dims_source is None:
        flag("warn", "dimensions_source_undeclared",
             "dimensions_source is not set — state \"declared\" or \"unknown\", "
             "don't leave it implicit")
    elif dims_source not in DIMENSIONS_SOURCE_VALUES:
        flag("fail", "fabricated_dimensions",
             f"dimensions_source `{dims_source}` is not one of {sorted(DIMENSIONS_SOURCE_VALUES)} "
             "— an estimated/guessed value is not an allowed provenance for this field")
    if dims_source == "unknown" and draft.get("dimensions"):
        flag("fail", "fabricated_dimensions",
             "dimensions_source is \"unknown\" but a dimensions object is populated — "
             "an unknown dimension must be reported as unknown, not filled in anyway")

    # certifications carried verbatim — the gate can't verify "verbatim" from
    # the JSON alone, but it can catch the shape that most often hides an
    # invented one: certifications present with no corresponding source note.
    certs = draft.get("certifications")
    if certs and not draft.get("certifications_verbatim"):
        flag("warn", "certifications_unconfirmed",
             "certifications are present but certifications_verbatim is not set true — "
             "confirm these were copied from the source listing, not generated")

    # pricing policy
    price = draft.get("price", {})
    src_amount = price.get("source_amount")
    dst_amount = price.get("destination_amount")
    if isinstance(src_amount, (int, float)) and isinstance(dst_amount, (int, float)) and src_amount:
        delta_pct = (dst_amount - src_amount) / src_amount
        declared_delta = price.get("delta_pct")
        if declared_delta is not None and abs(declared_delta - delta_pct) > 0.001:
            flag("warn", "delta_pct_mismatch",
                 f"declared delta_pct {declared_delta} does not match computed {delta_pct:.4f}")
        if abs(delta_pct) > PRICE_DELTA_CONFIRM_THRESHOLD and not price.get("price_change_confirmed"):
            flag("fail", "price_change_unconfirmed",
                 f"price delta {delta_pct:+.1%} exceeds the "
                 f"{PRICE_DELTA_CONFIRM_THRESHOLD:.0%} threshold and price_change_confirmed is not true")
    else:
        flag("warn", "price_amounts_incomplete",
             "price.source_amount/destination_amount missing or non-numeric — delta could not be checked")

    return _verdict(flags)


def _verdict(flags: list[dict]) -> dict:
    sevs = {f["severity"] for f in flags}
    verdict = "FAIL" if "fail" in sevs else ("WARN" if "warn" in sevs else "PASS")
    return {"verdict": verdict, "flags": flags,
            "next_step": ("hand_to_seller_for_review" if verdict != "FAIL" else "fix_draft")}


# ─────────────────────────── demo ───────────────────────────────────────────
GOOD_DRAFT = {
    "source_platform": "ozon",
    "destination_platform": "wildberries",
    "source_sku": "OZ-88213",
    "internal_id": "prod_4471",
    "status": "draft",
    "title": "Складной кухонный органайзер, 3 отсека",
    "description": "Компактный органайзер для хранения кухонной утвари...",
    "category": {"source_id": "17028094", "destination_id": "9012771",
                 "destination_path": "Дом > Кухня > Хранение"},
    "images": [{"url": "https://cdn.example/1.jpg", "position": 1},
               {"url": "https://cdn.example/2.jpg", "position": 2}],
    "source_image_count": 2,
    "images_omitted_reason": None,
    "dimensions": {"length_cm": 30, "width_cm": 20, "height_cm": 10},
    "weight_g": 450,
    "dimensions_source": "declared",
    "certifications": ["EAC"],
    "certifications_verbatim": True,
    "price": {"source_amount": 1490, "source_currency": "RUB",
              "destination_amount": 1690, "destination_currency": "RUB",
              "delta_pct": 0.1342, "price_change_confirmed": False},
}

BAD_DRAFT = {
    "source_platform": "ozon",
    "destination_platform": "wildberries",
    "source_sku": "",
    "internal_id": "prod_9981",
    "status": "published",
    "title": "Premium Wireless Widget",
    "description": "The best widget on the market, guaranteed to sell fast.",
    "category": {"source_id": "1002", "destination_id": None},
    "images": [{"url": "https://cdn.example/only-one.jpg", "position": 1}],
    "source_image_count": 5,
    "images_omitted_reason": None,
    "dimensions": {"length_cm": 12, "width_cm": 8, "height_cm": 4},
    "weight_g": 220,
    "dimensions_source": "unknown",
    "certifications": ["CE", "FCC"],
    "price": {"source_amount": 900, "destination_amount": 1500, "delta_pct": 0.667,
              "price_change_confirmed": False},
}


def demo() -> int:
    print("=" * 68)
    print("DEMO - cross-listing gate: a reviewable draft vs a premature publish")
    print("=" * 68)
    outcomes = {}
    for name, draft in (("kitchen_organizer_draft", GOOD_DRAFT), ("premature_publish", BAD_DRAFT)):
        rep = validate(draft)
        outcomes[name] = rep["verdict"]
        print(f"\n> {name}")
        for f in rep["flags"]:
            print(f"  [{f['severity'].upper():4}] {f['code']}: {f['detail']}")
        if not rep["flags"]:
            print("  (no flags)")
        print(f"  VERDICT: {rep['verdict']}  ->  {rep['next_step']}")
    ok = outcomes["kitchen_organizer_draft"] in ("PASS", "WARN") and outcomes["premature_publish"] == "FAIL"
    print("\n" + ("demo OK - the gate hands over a clean draft and refuses the broken one"
                  if ok else "demo UNEXPECTED - check implementation"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cross-listing draft completion gate")
    ap.add_argument("draft", nargs="?", help="path to DRAFT.json")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.draft:
        ap.error("provide DRAFT.json (or use --demo)")
    with open(args.draft) as f:
        draft = json.load(f)
    report = validate(draft)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["verdict"] in ("PASS", "WARN") else 1


if __name__ == "__main__":
    sys.exit(main())
