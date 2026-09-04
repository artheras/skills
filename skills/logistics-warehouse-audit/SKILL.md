---
name: logistics-warehouse-audit
description: >-
  Trigger this skill when the user asks to check logistics health, warehouse inventory, inbound exceptions, freight forwarder API status, or wants to draft a replenishment order (e.g., "Check warehouse MOS-01 inventory", "Are there any inbound exceptions?", "Check freight API latency", "Draft a replenishment order for SKU-9921").
  Do NOT trigger for standard coding or financial backtests.
---

# Warehouse & Logistics ERP Auditor

This skill enforces strict Standard Operating Procedures (SOPs) for the Logistics Agent when interacting with the enterprise ERP system. Its operational data comes only from the `warehouse-api` read model; it never reads the ERP database or a freight-provider credential directly.

## When this matters

- "Check the inventory health of MOS-01."
- "Why is the freight forwarder sync delayed?"
- "Are there any damaged goods from today's inbound shipments?"
- "Draft a restock order for SKU-9921."

## Workflow — order matters

1. **System Health Check**: Always start by checking `warehouse.logistics_sync_health` with `warehouseId` to ensure the freight forwarder API is not lagging (if the user is asking about inbound statuses).
2. **Context Retrieval**: Call `warehouse.inventory_health` or `warehouse.inbound_exception_review` with the same `warehouseId`.
3. **Risk Analysis**:
   - Highlight any SKUs where stock < min_stock.
   - Highlight any DAMAGED or QUANTITY_MISMATCH shipments.
4. **Action (Strict Rule)**:
   - If the user asks to replenish or move stock, call `erp.draft_replenishment_order` only when that approval-gated ERP tool has been installed.
   - **MANDATORY**: You MUST explicitly tell the user that the agent only creates a DRAFT and that human approval in the ERP frontend is strictly required, as per the Service Contract.

## Shared service contract

- Aria Code batch analysis reads `GET /api/v1/warehouses/{warehouse_id}/agent-snapshot` using its read-only service token.
- Arthera Terminal uses the three `warehouse.*` tools above with the signed-in user's identity.
- Both views are projections of the same authorized snapshot. If the snapshot is unavailable or stale, report that limitation and do not infer an inbound status.
