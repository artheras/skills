---
name: commerce-operations-agent
description: >-
  Operate approved Wildberries listing publication and FBS order cancellation
  under a seller-managed automation policy. Use for recurring e-commerce
  publishing or cancellation operations; not for catalog migration drafts.
---

# Commerce Operations Agent

Use this skill only after the seller has installed the commerce MCP server and
explicitly enabled the relevant capability in their local automation policy.
The Agent must never edit, create, or claim to enable that policy.

## Publishing

1. Call `commerce.automation.status`. Stop if automation, Wildberries, or
   listing auto-publish is disabled.
2. Read the draft using `drafts.get`. It must be a validated Wildberries
   cross-listing draft and include `wildberries_publish_payload` produced by a
   verified marketplace adapter. Do not invent or transform marketplace card
   fields at publish time.
3. Generate one new idempotency key for the requested operation; reuse the
   same key only when retrying that exact operation.
4. Call `commerce.automation.publish_wildberries_draft`. Report the operation
   ID and whether a retry was deduplicated.

## FBS cancellation

1. State the requested seller-approved reason and collect explicit order IDs.
   Never cancel based on a product title, fuzzy search, or inferred order.
2. Call `commerce.automation.status`. Stop if cancellation is disabled, the
   reason is not listed, or the batch exceeds the configured limit.
3. Generate an idempotency key and call
   `commerce.automation.cancel_wildberries_fbs_orders` once for the exact
   batch. The service performs a fresh status preflight and rejects the whole
   batch when any order is no longer eligible.
4. Do not retry a partial failure with a new key. Inspect the audit record and
   retry only the clearly uncompleted IDs with the original key when the seller
   directs it.

## Boundaries

- The policy is the authority boundary; the Agent cannot turn automation on.
- Publishing supports Wildberries only. OZON stays draft-only until a verified
  product-import adapter is available.
- Do not expose marketplace tokens, policy-file contents outside the requested
  summary, or raw API credentials.
- `cross-listing` remains the correct skill to create or validate migration
  drafts. This skill performs the separately authorised operational step.
