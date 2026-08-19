---
name: logistics-warehouse-audit
description: >-
  Trigger this skill when the user asks to check logistics health, warehouse inventory, inbound exceptions, freight forwarder API status, or wants to draft a replenishment order (e.g., "Check warehouse MOS-01 inventory", "Are there any inbound exceptions?", "Check freight API latency", "Draft a replenishment order for SKU-9921").
  Do NOT trigger for standard coding or financial backtests.
---

# Warehouse & Logistics ERP Auditor

This skill enforces strict Standard Operating Procedures (SOPs) for the Logistics Agent when interacting with the enterprise ERP system. Based on the `AGENT_SERVICE_CONTRACT`, the agent operates in a strictly governed environment.

## When this matters

- "Check the inventory health of MOS-01."
- "Why is the freight forwarder sync delayed?"
- "Are there any damaged goods from today's inbound shipments?"
- "Draft a restock order for SKU-9921."

## Workflow — order matters

1. **System Health Check**: Always start by checking `check_logistics_sync_health` to ensure the freight forwarder API is not lagging (if the user is asking about inbound statuses).
2. **Context Retrieval**: Call `check_inventory_health` or `check_inbound_exceptions` for the requested warehouse.
3. **Risk Analysis**:
   - Highlight any SKUs where stock < min_stock.
   - Highlight any DAMAGED or QUANTITY_MISMATCH shipments.
4. **Action (Strict Rule)**:
   - If the user asks to replenish or move stock, call `draft_replenishment_order`.
   - **MANDATORY**: You MUST explicitly tell the user that the agent only creates a DRAFT and that human approval in the ERP frontend is strictly required, as per the Service Contract.
