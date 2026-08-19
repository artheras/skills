---
name: devops-incident-responder
description: >-
  Trigger this skill when the user asks to investigate an IT incident, server error, database crash, or requests automated troubleshooting and service recovery (e.g., "Check open IT tickets", "Fix the PostgresDB connection error", "Restart the failed quant service").
  Do NOT trigger for standard market data or quantitative backtesting requests.
---

# DevOps Automated Incident Responder

This skill elevates the Agent from a "read-only assistant" to an **Agentic Process Automation (APA)** operator capable of full-loop self-healing operations.

## When this matters

- "Are there any open IT incidents?"
- "Check the PostgresDB error INC-890 and fix it."
- "The Quant Engine ran out of memory, please resolve the ticket and restart."

## Workflow — order matters

1. **Triage & Diagnosis**:
   - Use `query_enterprise_knowledge_base` (domain: `IT_INCIDENTS`) to fetch error logs for the specific incident ID or system.
   - Analyze the root cause (e.g., connection limits reached, out of memory).
2. **Mitigation / Self-Healing Execution**:
   - If a service restart is sufficient to clear the error state (like connection pool exhaustion), call the `restart_enterprise_service` tool on the affected service.
   - (If configuration changes are needed, the agent could theoretically use its native `run_command` or `edit_file` tools to modify local docker-compose settings before restarting).
3. **Closing the Loop (Write-back)**:
   - Call `update_it_ticket_status` to change the incident status to "Resolved" and log exactly what was done in the `resolution_notes`.
4. **Debrief**:
   - Report back to the user with a summary of the root cause, the actions taken, and confirmation that the ticket is closed.
