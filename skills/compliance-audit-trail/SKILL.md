---
name: compliance-audit-trail
description: >-
  Validate a model/strategy governance manifest before it goes to a
  counterparty, investor, or internal reviewer doing real due diligence.
  Trigger for "尽调清单", "due diligence", "model governance", "compliance
  audit trail", "机构接入前会问什么", "这个系统靠不靠谱", "写一份治理文档",
  "risk control 真的在跑吗", "audit trail", "监管合规", or whenever the user
  is about to claim a system is validated/production-ready/risk-managed to
  someone outside the team, or is drafting the kind of document that answers
  how the system is validated, whether risk control is actually running, and
  where its boundaries are. Also trigger when a risk control, circuit breaker,
  or safety mechanism is being marked as finished — this skill’s job includes
  catching the gap between code that exists and code that has been verified
  to actually trigger, which is the single most common false claim in this
  category. Do NOT trigger for the underlying research/risk/backtest work
  itself — `backtest-validation`, `risk-assessment`, and
  `multiple-testing-correction` produce the evidence; this skill checks that
  evidence is honestly compiled and disclosed, not that the underlying work is
  correct.
---

# Compliance Audit Trail

A governance document is a set of claims. Prose claims are worth nothing to
someone doing real due diligence — they need to know which claims are
checkable, which production assets actually cleared every gate the system
itself says is required, whether a declared risk control has ever been
verified to actually fire, and what the honestly-disclosed boundaries are.
This skill validates a structured manifest against exactly those questions,
mechanically, so "we have a compliance audit trail" becomes a checkable claim
instead of another sentence in the document.

## The gap this closes

The most common failure mode in this category is not lying — it is
conflating "the code for X exists" with "X has been verified to actually
happen." A circuit breaker that has never received real NAV data, or whose
peak-tracking comparison has an inverted sign, will sit in the codebase
looking exactly like a working circuit breaker until someone actually runs
data through it end to end and watches it trip. A governance document written
from the code (`grep -l circuit_breaker`) will say "risk control: implemented."
A governance document written from a real, run test will say "risk control:
implemented and verified to trigger [evidence: integration test log]." Those
are different claims, and only the second one survives real due diligence.

## Workflow

1. Compile the manifest from evidence, not memory. Every entry in
   `capability_claims` needs a real pointer (file path, test name, dashboard
   link) — if you cannot point at it, it is not ready to claim. See
   `references/manifest-schema.md` for the exact schema.
2. For `production_scope`, list only assets/strategies/models that have
   actually cleared every gate named in `required_gates` — not everything
   with a trained model file or a backtest that ran once. If in doubt, it
   goes in a research/pending list, not production scope.
3. For each `risk_controls` entry marked `declared_present: true`, only set
   `verified_triggering: true` if there is a real test (ideally end-to-end,
   against real infrastructure, not mocked) that watched the control
   actually fire. If that test does not exist yet, mark it `false` — that is
   a WARN-worthy honest gap, not a FAIL-worthy lie.
4. Run the gate: `python scripts/governance_manifest_gate.py manifest.json`.
   With no manifest at hand, see the mechanics with `--demo`.
5. Fix FAIL-severity flags before this document goes anywhere external —
   `unverifiable_claim`, `production_scope_gate_missing`,
   `unverified_safety_mechanism`, and `no_audit_trail` are the kind of gaps
   that make a due-diligence reviewer stop trusting the rest of the document
   the moment they find one.
6. WARN-severity flags (`compliance_gap`, `no_limitations_disclosed`,
   `stale_manifest`, thin evidence) do not block sharing the document, but
   report them as open items rather than silently omitting them — an honest
   "here's what's not done yet" section is itself evidence of a functioning
   governance process.
7. Completion gate: a manifest is fit to hand to a counterparty only when the
   gate exits 0 (PASS or WARN). Never characterize a FAIL-verdict manifest as
   "our system is fully governed" — the correct framing is "here is our
   current governance state and the gaps we're closing," which is what
   sophisticated counterparties actually want to see.

## Guardrails

- Never mark `verified_triggering: true` on a control that has only been
  read in the source code, not watched to actually fire.
- Never list an asset in `production_scope` on the strength of "we have a
  model for it" alone — it needs the gates.
- An empty `known_limitations` list is a flag, not a clean bill of health
  (see `references/manifest-schema.md` for why) — do not clear this warning
  by writing filler limitations; write real ones or leave the warning.
- This skill validates disclosure structure, not the truth of the underlying
  evidence — it cannot catch a fabricated evidence pointer. Pair with the
  skill that actually produced the evidence (`backtest-validation` for
  performance claims, `risk-assessment` for risk claims,
  `multiple-testing-correction` for significance claims) so the pointer
  resolves to something real.

## Bundled resources

- `scripts/governance_manifest_gate.py` — the manifest validator, stdlib
  only. `--demo` runs a disclosed manifest against a hollow one with the
  same claims and no evidence, and shows the gate separate them.
- `references/manifest-schema.md` — the full field-by-field schema and the
  reasoning behind the one rule that inverts the usual "empty = fine"
  instinct (empty `known_limitations`).
