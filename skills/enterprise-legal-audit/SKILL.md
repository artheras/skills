---
name: enterprise-legal-audit
description: >-
  Trigger this skill when the user asks to review, audit, or check the risks of an internal corporate contract, legal agreement, or vendor SLA (e.g., "Audit the Stripe contract", "Are there any high-risk clauses in our pending vendor agreements?").
  Do NOT trigger for standard coding, financial backtests, or market data queries.
---

# Enterprise Legal Contract Audit

This skill enforces discipline and standard operating procedures (SOPs) when evaluating third-party vendor contracts or enterprise SLAs. A naive read of a contract might miss specific liability clauses or auto-renewal traps that legal teams look for.

## When this matters

- "Run a legal audit on contract CONT-2026-042"
- "Are there any infinite liability risks in our recent AWS or Stripe contracts?"
- "Review the terms for the new office lease."

## Workflow — order matters

1. **Information Retrieval**: Call the `query_enterprise_knowledge_base` tool (provided by the Enterprise RAG MCP server) using the domain `LEGAL_CONTRACTS` to fetch the specific contract metadata and text.
2. **Automated Clause Scanning**: Call the `audit_legal_contract` tool with the contract ID to run the algorithmic risk flags (catching Unlimited Liability or Auto-renewal traps).
3. **Synthesis & Final Review**:
   - If ANY high-risk flags are returned (e.g., UNLIMITED LIABILITY), strictly advise the user that the contract MUST be routed to the human General Counsel for manual sign-off.
   - Output the final risk report clearly indicating **[PASS]**, **[WARN]**, or **[FAIL]**.

## Bundled resources

- None. This skill relies entirely on the external `Enterprise Lakehouse & RAG` MCP server being connected to the agent.
