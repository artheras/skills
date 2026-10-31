---
name: factor-research
description: >-
  Evaluate whether a cross-sectional factor genuinely predicts returns.
  Trigger for "这个因子有效吗", "算一下IC", "动量因子在A股还有效吗",
  "帮我评估这个选股信号", "factor IC", "is this signal predictive",
  "compare momentum vs value factors", or whenever the user (1) proposes or
  computes a ranking/score across assets and asks if it works, (2) asks which
  factor explains recent moves, (3) wants factors screened/ranked before
  building a strategy, or (4) hands a signal to strategy construction. Fire
  even for informal phrasing ("这个指标选股靠谱吗"). Do NOT trigger for
  single-asset technical indicator questions (no cross-section) or for
  validating a finished strategy’s returns (that is backtest-validation).
---

# Factor Research

A factor is a claim that an ordering of assets today predicts their returns
tomorrow. Rankings are cheap — every column of numbers orders a universe. This
skill measures whether the ordering carries information, how fast it decays,
and whether it survives its own turnover.

## Position in the pipeline

`point-in-time-research` guards the data that builds the factor panel. This
skill judges the panel. Survivors go to `backtest-validation`, where costs and
selection bias get their turn. **A factor evaluated on contaminated data has a
fictional IC — run PIT discipline first if the panel provenance is unclear.**

## What gets measured (one way, no options)

1. **Rank IC series** — per-period cross-sectional Spearman of factor(t) vs
   next-period returns. Rank, not Pearson: factors are orderings, and Pearson
   IC is one outlier away from flattery. Mean IC, IC-IR, t-stat, hit rate.
2. **Decay** — mean IC at 1/5/10/21-period horizons. Fast decay + high
   turnover = the edge pays the broker.
3. **Quantile discipline** — mean forward return per quintile and the share of
   ordered adjacent steps. A real factor orders the middle of the book, not
   just the two extreme buckets.
4. **Stability** — first-half vs second-half IC (a sign flip is fatal) and
   factor rank autocorrelation (turnover proxy).

## Workflow

1. Establish the panel: factor values as-of each date (long format
   date,symbol,value), the return matrix, the frequency, and where the factor
   values came from. If provenance is unclear, route through
   point-in-time-research before trusting any IC.
2. Run `python scripts/factor_evaluate.py --factor factor.csv --returns returns.csv --freq daily --json report.json`
   (or `--demo` to show the mechanics).
3. Report judgement first, then the evidence: IC/IR/t/hit-rate, decay curve,
   quantile spread, turnover. Interpretation thresholds live in
   `references/methodology.md`.
4. Route by verdict: `valid` / `valid_but_moderate` → hand to
   backtest-validation (the factor is a hypothesis, not yet a strategy);
   `weak` / `invalid` → the deliverable is the rejection and which check
   failed. Do not "fix" a dead factor by trying variants until one passes —
   that is selection bias, and backtest-validation's DSR will ask how many
   variants were tried.
5. When comparing multiple factors, evaluate each on the same universe and
   window, and report the count of factors examined alongside the winner.

## Guardrails

- IC below noise threshold is reported as "no signal", never rounded up to
  "slightly positive".
- No strategy construction on a `weak`/`invalid` verdict.
- Multiple factors tried = trials disclosed downstream to backtest-validation.
- Decay and turnover are always reported together — a horizon-1 edge with
  churny ranks is flagged, not celebrated.
