---
name: operator-revenue-integrity
description: >-
  Verify an operator’s or tenant’s self-reported revenue before it is used to
  settle a revenue-share, guarantee, or performance clause. Trigger for
  "核实流水", "商户流水是不是真的", "这个月分账对不对", "怀疑商户漏报流水",
  "能耗和流水对不上", "verify operator revenue", "tenant underreporting
  sales", "revenue share settlement check", or whenever a payout depends on a
  number the counterparty reported themselves. Do NOT trigger for public-market
  or securities analysis — declared-revenue verification for a private operator
  is a different problem from equity research (use `equity-research-report`),
  and this skill has no opinion on whether a business is a good investment,
  only on whether the number it reported is supportable.
---

# Operator Revenue Integrity

In an operating-rights or revenue-share arrangement (经营权共创), the operator
reports the revenue that determines what they owe. That number is the single
figure in the whole relationship they have a direct incentive to understate,
and it arrives with no adversarial review attached.

The naive check is to compare declared revenue against the operator's own POS
or payment records. That is not verification — POS terminals, payment QR codes,
and bookkeeping are all inside the operator's control. An operator routing
customers to a personal payment code (私账) produces POS records that are
internally consistent and understated at the same time. Consistency with a
source the counterparty controls is not evidence.

**Only signals outside the operator's control are independent evidence**:
utility meters, door-access and parking logs, foot-traffic counters,
delivery-platform settlement records (paid by the platform, not the operator),
and inventory deliveries visible to the landlord. Verification means checking
the declared figure against those, and treating a gap as a finding rather than
noise.

## Workflow

1. **Inventory the evidence by who controls it.** Before computing anything,
   split available data into operator-controlled (declared revenue, POS,
   own bookkeeping) and independent (utilities, access logs, foot traffic,
   platform settlements, inventory). If nothing independent is available, say
   so and stop — a verification report built only from operator-controlled
   data is worse than no report, because it launders an unchecked number into
   something that looks audited.
2. **Cross-verify the declared figure** — the `cashflow_verify` agent
   reconciles declared revenue against POS, bank, delivery, and
   inventory-implied revenue, and flags the gaps.
3. **Check the physical signals** — the `energy_anomaly` agent reads utility
   consumption, access records, and foot traffic. Read
   `references/independent_signals.md` for what each signal can and cannot
   establish; several have specific failure modes that produce false alarms.
4. **Aggregate into risk** — the `fulfillment_risk` agent combines
   verification findings with contract-side facts (overdue invoices, deposit
   shortfall, unauthorized account changes).
5. **Only then compute the settlement** — `revenue_share` applies the
   contract's floor and sharing terms. Never settle on a declared figure that
   failed step 2 or 3 without recording the discrepancy alongside the payment.
6. **Report on the health scale**, not a trading scale: `GOOD` / `WATCH` /
   `CONCERN` / `SEVERE`. See `agents/signal_scheme.py::REALTY_SCHEME` in Aria
   Code — these agents deliberately do not speak in BUY/SELL, because
   "cash flow is genuine" and "buy this stock" are not the same axis.

## Guardrails

- **A gap is a finding, not a verdict.** Energy-to-revenue ratios move for
  legitimate reasons — a change of business format, a new freezer, a seasonal
  menu. Report the discrepancy and its size; do not assert fraud. The output
  of this skill is evidence for a conversation with the operator, not an
  accusation.
- **Never state a confidence that the evidence does not support.** One
  independent source is weak corroboration; the agents scale confidence with
  the number of independent sources present, and so should the write-up.
- **Do not accept "POS matches declared" as verification.** Say explicitly
  which independent sources were checked and which were unavailable.
- **Absence of a signal is not absence of a problem.** No utility data means
  unverified, not clean.

## Bundled resources

- `references/independent_signals.md` — what each independent signal
  establishes, its specific false-alarm modes, and the thresholds the agents
  use.
