---
name: cross-listing
description: >-
  Migrate a product listing from one marketplace to another (OZON ↔
  Wildberries today) as a validated draft — never a live publish. Trigger for
  "把这个 OZON 商品同步到 WB", "跨平台上架", "这批商品搬到另一个平台",
  "migrate this listing to Wildberries", "cross-list this product", "sync my
  OZON catalog to WB", or whenever a user wants a product replicated onto a
  second marketplace with translated or reformatted metadata. Do NOT trigger
  for editing a listing on its own marketplace (no migration involved), or for
  publishing a listing — this skill never publishes on its own, only drafts.
---

# Cross-Marketplace Listing

Moving a listing between marketplaces looks like a copy-paste job and fails
like one: categories don't line up 1:1 between platforms, required attributes
differ per destination, and a naive price copy ignores the commission and
logistics-cost difference between them. This skill turns "move it over" into
a validated draft the seller reviews before anything goes live — one
direction is wired today (OZON ↔ Wildberries), built so a third marketplace
is a new adapter to `references/listing-schema.md`, not a rewrite of the
workflow.

## Authority boundary (read first)

The gate's output is a `status: "draft"` listing. **Publish is never this
skill's action.** A draft whose `status` field reads anything other than
`draft`/`pending_review` FAILS the gate mechanically — the same
mechanical-refusal shape as `execution-position`'s `paper_only` intent and
`strategy-generation`'s ban on a `live` status. This is structural, not just
written guidance: `skill-policy.json`'s `allowed_tools` deliberately does not
list a publish-capable tool (`ozon.publish_listing`, `wb.publish_listing`) —
the skill has no way to call one even if instructed to. The seller publishes
from the destination marketplace's own console, or a separate,
explicitly-approved publish action outside this skill's scope.

## Workflow — order matters

1. **Retrieve the source listing** — full attributes, images, price,
   category, dimensions/weight, and any certifications. Never re-derive a
   field the source listing already states.
2. **Fetch media** — download every image. A destination draft with fewer
   images than the source needs a disclosed `images_omitted_reason`, not a
   silent drop.
3. **Normalize into the canonical schema** (`references/listing-schema.md`)
   before touching either marketplace's own field names — this is what keeps
   a third marketplace an adapter instead of a parallel workflow.
4. **Map the category** — source category → destination category ID. No
   confident match is a FAIL, not a best-guess placeholder category.
5. **Rewrite title and description for the destination marketplace's language
   and conventions** — translate, don't transliterate, and never add a claim
   the source description didn't make.
6. **Carry dimensions, weight, and certifications verbatim.** Never invent a
   dimension, weight, or certification the source doesn't declare — an
   unknown value is reported as unknown (`dimensions_source: "unknown"`), not
   filled with a plausible-looking number to satisfy a required field.
7. **Apply the pricing policy** — compute the delta versus the source price.
   A delta beyond ±15% requires the seller's explicit confirmation
   (`price_change_confirmed: true`) before the draft can pass; anything
   inside that band is fine to carry automatically.
8. **Run `python scripts/validate_listing_draft.py DRAFT.json`** (or
   `--demo`). On PASS/WARN: present the draft plus every flag verbatim — a
   `price_change_confirmed` reminder is as important as the draft itself. On
   FAIL: the deliverable is the refusal and the specific missing or invalid
   field — never a draft that quietly drops a required attribute to slip
   past the gate.
9. **Preserve linkage** — `source_platform`, `source_sku`/`internal_id`, and
   the destination draft ID all travel together in the record, so the two
   listings stay traceable to each other after publish.
10. Hand the validated draft back for the seller's review. Calling an
    explicit "create draft" tool on the destination marketplace is fine;
    calling a publish tool is not this skill's job under any flag,
    instruction, or user insistence — see Authority boundary above.

## Guardrails

- `status` on every draft is `draft` or `pending_review` — a `published`/`live`
  status fails mechanically, same shape as `execution-position`'s refusal of
  live orders.
- No category match → FAIL, never a guessed category.
- No fabricated dimensions, weight, or certifications — unknown is reported
  as unknown, never estimated to fill a required field.
- Price delta beyond ±15% needs `price_change_confirmed: true`; unconfirmed
  FAILs the gate.
- Missing images are declared via `images_omitted_reason`, never silently
  dropped from the draft.
- `source_sku`/`internal_id` must be present on every draft — losing the link
  back to the source listing is treated the same as losing the listing.
