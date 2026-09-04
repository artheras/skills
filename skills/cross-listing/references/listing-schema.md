# Canonical listing draft schema

One JSON object per draft. Every marketplace adapter (OZON, Wildberries,
and whatever comes after them) reads and writes this shape — a listing never
travels between platforms in either marketplace's own field names. The
validator (`scripts/validate_listing_draft.py`) enforces the fields marked
**required** and the honesty fields marked **disclosure**.

```jsonc
{
  "source_platform": "ozon",             // required
  "destination_platform": "wildberries", // required
  "source_sku": "OZ-88213",              // required — linkage back to source
  "internal_id": "prod_4471",            // required — Arthera's own product id

  "status": "draft",                     // required — "draft" | "pending_review" ONLY.
                                          // Anything else (e.g. "published", "live")
                                          // fails the gate mechanically.

  "title": "...",                        // required, destination-language
  "description": "...",                  // required, destination-language

  "category": {
    "source_id": "17028094",
    "destination_id": "9012771",         // required — null/absent = unmapped = FAIL
    "destination_path": "Home > Kitchen > Storage"
  },

  "attributes": {                        // destination-marketplace required fields,
    "...": "..."                         // varies per category — see the
  },                                      // marketplace's own attribute schema

  "images": [
    {"url": "https://...", "position": 1}
  ],
  "source_image_count": 6,
  "images_omitted_reason": null,         // disclosure — required non-null if
                                          // images.length < source_image_count

  "dimensions": {"length_cm": 30, "width_cm": 20, "height_cm": 10},
  "weight_g": 450,
  "dimensions_source": "declared",       // disclosure — "declared" (from source
                                          // listing) | "unknown". Never "estimated"
                                          // with a made-up number.

  "certifications": ["EAC"],             // carried verbatim from source, or omitted
                                          // if the source has none — never invented

  "price": {
    "source_amount": 1490,
    "source_currency": "RUB",
    "destination_amount": 1690,
    "destination_currency": "RUB",
    "delta_pct": 0.134,                  // (destination - source) / source
    "price_change_confirmed": false      // disclosure — required true if
                                          // abs(delta_pct) > 0.15
  }
}
```

## Why these fields and not others

- **`status` is the publish gate.** It is the one field the skill's own
  Authority boundary depends on — see `SKILL.md`. A draft record with any
  other value is not a bug in the record, it is a policy violation.
- **`dimensions_source`/`images_omitted_reason`/`price_change_confirmed`
  are disclosure fields, not data fields.** They exist so a downstream
  reviewer (human or another skill) can tell the difference between "this
  listing genuinely has no extra images" and "the migration silently dropped
  three of them."
- **`category.destination_id` has no fallback.** A migration that files a
  product under the wrong category is worse than one that stops and asks —
  wrong-category listings get suppressed in search on most marketplaces,
  which reads to the seller as "the sync worked" right up until GMV doesn't
  show up.
