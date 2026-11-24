---
name: gamma-exposure
description: >-
  Compute or review a Gamma Exposure (GEX) / dealer-hedging-behavior
  estimate from options open interest before it gets reported as if it
  were an observed fact. Trigger for "gamma exposure", "GEX chart", "GEX
  level", "GEX profile", "gamma squeeze", "gamma wall", "zero gamma flip",
  "dealer positioning", "做市商对冲", "伽马敞口", "波动率压制/放大",
  "0DTE flows", "净伽马敞口", or whenever the user is inferring
  options-dealer hedging pressure from open interest and implied volatility,
  building a GEX chart/panel, or about to state a GEX regime call (dealers
  are long/short gamma at some strike) as if it were measured rather than
  estimated under an assumption. Also trigger when reviewing GEX-computation
  code for a silent sign or scaling bug — the failure mode this skill exists
  to catch produces a plausible-looking wrong answer, not a crash. Do NOT
  trigger for a plain options-chain display (bid/ask/volume/greeks per
  contract, no hedging inference) or for risk exposure of options the user
  actually holds — that is `risk-assessment`.
---

# Gamma Exposure (GEX)

GEX infers options-dealer hedging *behavior* — not dealer hedging
*positions*, which are never public — from open interest, implied
volatility, and one industry-standard but fundamentally unverifiable
assumption. Every number this produces is an estimate under that
assumption, and the single most common failure in this category is
reporting it as a fact instead.

## The gap this closes

GEX computations look deceptively easy to get right: sum some gammas,
apply a scaling constant, done. Two things make it easy to get quietly
wrong instead:

1. **The sign convention is an assumption, not a physical law.** The
   standard convention — customers are net buyers of options, dealers are
   net sellers, so call OI contributes positive gamma exposure and put OI
   contributes negative — is a public-GEX-calculator convention (the same
   one SqueezeMetrics-style tools use), not something derivable from the
   options data itself. Flip that one sign and the code still runs, still
   produces a smooth chart, and still gives a *confident* regime call —
   just the opposite one from what the data implies under the standard
   assumption. `scripts/gex_gate.py --demo` reproduces this exact bug on
   one synthetic chain: identical inputs, `net_gex_total` flips from
   -1.08M to +2.63M, regime flips from negative to positive.
2. **The assumption itself is presented as measured fact.** No public
   dataset shows dealers' actual positioning. A report that states "dealers
   are short gamma at 450" without the caveat is making a stronger claim
   than the data supports — the honest version is "under the standard
   assumption that dealers are net short customer flow, OI implies dealers
   are short gamma at 450."

## Workflow

1. Get a real option chain — strike, open interest, and implied volatility
   for both legs at each strike, for one expiration. Free listed-equity
   data (e.g. yfinance) is enough; do not fabricate OI/IV to fill gaps.
2. Compute gamma per strike with the standard Black-Scholes closed form
   (`scripts/gex_gate.py`'s `black_scholes_gamma`) — identical for calls
   and puts at the same (S, K, T, sigma), so there's no separate call/put
   gamma formula to get wrong.
3. Apply the standard sign convention (call OI: +, put OI: -) and the
   standard normalization (`Γ × OI × contract_multiplier × S² × 0.01`) —
   see `references/methodology.md` for why that specific scaling. Do not
   invent a different convention or scaling without calling it out as
   non-standard.
4. Attach both disclosures to the output every time, not just in an
   appendix: the dealer-positioning assumption, and what this snapshot
   does NOT cover (other expirations, intraday OI changes since the
   snapshot, OTC/index flow that free listed-equity data can't see).
5. Before sharing a GEX report, run it through the audit gate:
   `python scripts/gex_gate.py --audit report.json`. FAIL-severity flags
   (`missing_dealer_assumption_disclosure`, `missing_coverage_limitation`,
   `gex_sum_mismatch`, `regime_sign_mismatch`, `flip_point_out_of_range`,
   `gamma_walls_mismatch`) mean the report is either undisclosed or
   internally inconsistent — fix before sharing, don't caveat around it.
6. `sparse_chain` (WARN) does not block sharing, but disclose it: a
   zero-gamma flip or gamma-wall pick computed from fewer than 5 strikes
   has real resolution limits worth stating next to the number.
7. See the sign-bug and disclosure-gate mechanics with no data at all:
   `python scripts/gex_gate.py --demo`.

## Guardrails

- Never state a GEX regime as an observed fact. It's always "under the
  standard assumption that dealers are net short customer flow, OI
  implies X" — not "dealers are X."
- Never silently choose a non-standard sign convention or scaling
  constant. If you have a specific reason to deviate from the industry
  standard, say so explicitly and explain why — don't let it look like
  the same convention everyone else uses.
- Never present GEX as a directional price forecast. It describes a
  hedging-flow *regime* (positive = dealer hedging tends to dampen
  volatility; negative = tends to amplify it), not a prediction of where
  price goes next.
- Never claim free listed-equity-options GEX covers a symbol's full
  dealer hedging book — OTC and index-option flow are frequently the
  larger piece and are invisible to this data source.
- A report with disclosures present is not automatically trustworthy —
  `audit_gex_report` also checks the numbers agree with each other
  (`gex_sum_mismatch`, `regime_sign_mismatch`) so a stale or hand-edited
  summary doesn't slip through just because the boilerplate caveat is
  there.

## Bundled resources

- `scripts/gex_gate.py` — `compute_gex()` (Black-Scholes-based, standard
  sign convention and normalization) plus `audit_gex_report()`, the
  disclosure/consistency gate. `--demo` reproduces the sign-convention bug
  flipping a regime call on identical inputs, then shows the gate separate
  a compliant report from a hollow one and catch a tampered summary.
- `references/methodology.md` — the gamma formula, the normalization
  constant and why it's there, the sign convention and its limits,
  zero-gamma-flip interpolation, gamma-wall selection, and what this
  estimate structurally cannot see.
