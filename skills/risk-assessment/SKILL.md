---
name: risk-assessment
description: >-
  Decompose and judge the risk of a portfolio, strategy, or single position
  from its actual history. Trigger for "我的组合风险大吗", "最大回撤会有多深",
  "如果市场跌20%我亏多少", "该不该降仓", "组合太集中了吗", "portfolio risk",
  "value at risk", "在险价值", "stress test my holdings", or whenever the user
  (1) holds or proposes a set of positions and asks how risky it is, (2) asks
  what a market drop would do to them, (3) asks whether to
  reduce/hedge/diversify, or (4) receives a strategy from another skill and
  needs its risk characterized before acting. Fire even for casual phrasing
  ("这样拿着安全吗", "is this too much NVDA?"). Do NOT trigger for backtest
  trustworthiness questions (that is backtest-validation) or pure data
  lookups.
---

# Risk Assessment

Risk questions deserve numbers a risk committee would accept — not vibes, and
not fabricated precision. This skill decomposes where the risk actually comes
from (volatility, concentration, correlation, tail shape) and states plainly
what the data cannot show.

## Principles

1. **Only the supplied history speaks.** Every figure is computed from the
   portfolio's own return window. No assumed correlation matrices, no invented
   scenarios. If the sample never contained a crisis, say that the numbers
   understate crisis risk — do not simulate one silently.
2. **Concentration is the risk most users cannot see.** Ten highly-correlated
   names are one position in disguise. Effective N and average pairwise
   correlation are reported next to VaR, always.
3. **The tail is not normal.** Historical VaR/CVaR and a Cornish–Fisher
   adjustment are shown together; when skew/kurtosis diverge from normal, the
   report says which number to trust less.
4. **Beta shocks are labeled as linear approximations.** A −20% market shock
   estimate via beta is a floor, not a ceiling — real crashes raise
   correlations. The report says so verbatim, and omits the shock table
   entirely when no benchmark is supplied.

## Workflow

1. Assemble inputs: per-asset return history (wide CSV), portfolio weights,
   optional benchmark. If weights don't sum to 1, the harness re-normalizes by
   gross exposure and **discloses it** — confirm with the user that gross
   exposure is what they meant.
2. Run the profile:
   `python scripts/risk_profile.py --returns returns.csv --weights weights.csv [--benchmark bench.csv] --json report.json`
   With no data, demonstrate with `--demo`.
3. Report in this order: risk level → main risk source → the flag list → core
   metrics → concentration/diversification → worst historical windows → beta
   shock estimate (if available). Lead with the diagnosis, not the table.
4. Translate flags for the user (see `references/methodology.md` for the
   thresholds and their rationale). "diversification_illusion" matters more to
   a retail holder than the CVaR decimal.
5. Any recommendation (reduce, hedge, diversify) must be framed as a research
   observation with its trigger flag attached — never as individualized
   investment advice. High-risk verdicts require explicit user confirmation
   before any downstream skill acts on them.
6. Always surface the `disclosure` lines from the report output. They are part
   of the deliverable, not boilerplate to trim.

## Guardrails

- No fabricated stress scenarios, correlations, or forward-looking loss
  estimates beyond the labeled linear beta approximation.
- No "safe", "guaranteed", or "risk-free" language, at any risk level.
- Missing inputs degrade honestly (`skipped` + reason), never silently.
- A "low" risk level describes the sample window, not the future — say so.
- Position-reduction suggestions are observations tied to flags; execution
  decisions belong to the user.
