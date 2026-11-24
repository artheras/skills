---
name: supply-chain-knowledge-graph
description: >-
  Trigger this skill when a user asks to analyze the supply chain, dependencies, suppliers, customers, or fundamental knowledge graph of a specific company (e.g., "Analyze Apple's supply chain risks", "Who supplies NVDA?", "What is the upstream/downstream impact on TSMC?").
  Do NOT trigger for standard technical analysis or price volume queries.
---

# Supply Chain & Knowledge Graph Analysis

This skill enforces the discipline of multi-node alternative data analysis. When evaluating a single asset, naive analysis only looks at the company's own financials. Professional quantitative analysis maps the company's dependency graph (Upstream Suppliers, Downstream Customers, Competitors) to identify delayed volatility shocks, inventory bullwhip effects, and hidden geopolitical risks.

## When this matters

- "Analyze Apple's supply chain risks"
- "If ASML misses earnings, who gets hit downstream?"
- "Map the AI hardware supply chain starting from NVDA"
- "What are the upstream dependencies for Tesla?"

## Workflow — order matters

1. **Entity Resolution**: Map the target ticker to its canonical corporate entity.
2. **Graph Expansion**: Call the `supply_chain_mapper.py` script to generate a 2-hop dependency graph (Upstream/Downstream).
3. **Risk Propagation Assessment**:
   - Check if any single upstream supplier accounts for >15% of COGS (Concentration Risk).
   - Check if downstream customers are facing macro headwinds (Demand Destruction Risk).
4. **Synthesis**: Present the findings in a structured Knowledge Graph Markdown format, explicitly labeling **[Upstream]**, **[Target]**, and **[Downstream]**.

## Bundled resources

- `scripts/supply_chain_mapper.py` — A runnable harness that simulates knowledge graph node extraction and calculates concentration risks. Run with: `python scripts/supply_chain_mapper.py --demo`
