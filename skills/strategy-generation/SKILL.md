---
name: strategy-generation
description: >-
  Turn a natural-language trading idea into a disciplined, testable strategy
  spec and implementation. Trigger for "帮我生成一个动量策略",
  "写一个BTC均值回归策略", "设计多因子选股", "做一个ETF轮动", "generate a
  momentum strategy", "build me a trading strategy", "turn this idea into
  code", or whenever the user (1) describes a trading idea and wants it made
  concrete, (2) asks for strategy code, (3) wants strategy variants compared,
  or (4) asks to improve an existing strategy. Fire even for vague asks
  ("有什么好策略推荐吗" — the answer is a disciplined spec, not a tip). Do NOT
  trigger for validating an already-backtested result (backtest-validation)
  or for pure factor evaluation (factor-research).
---

# Strategy Generation

A strategy that exists only as prose is a mood. This skill converts ideas into
specs that machines can refuse, code that gates can check, and claims that
survive the validation pipeline — or die there honestly.

## The pipeline (six stages, three gates)

```
IDEA → SPEC ──gate 1──→ CODE → RETURNS ──gate 2──→ RISK ──gate 3──→ PAPER
        │                          │                  │
        │ validate_strategy_spec   │ backtest-        │ risk-assessment
        │ (this skill's script)    │ validation       │ profile
```

1. **DATA** — establish market, universe, frequency, history budget, and
   whether the data pipeline is PIT-reviewed (`point-in-time-research`).
2. **SPEC** — fill the contract in `references/spec-schema.md`: named
   archetype, testable entry/exit logic, explicit parameters, at least one
   hard risk control, a cost assumption in bps, and `variants_tried`.
3. **Gate 1** — `python scripts/validate_strategy_spec.py SPEC.json`.
   FAIL means fix the spec; do not write code around a broken spec.
4. **CODE** — implement exactly the spec. Parameters come from
   `signal.parameters`, not from numbers invented mid-implementation. If
   implementation forces a change, update the spec and re-run gate 1.
5. **Gate 2** — produce the returns series and run it through
   `backtest-validation` with `--trials` = the spec's `variants_tried`
   (updated if more variants were tried during coding — honesty compounds).
   A FAIL verdict is a result: report it, don't tune until it passes.
6. **Gate 3** — run `risk-assessment` on the surviving equity curve and
   holdings. High-risk verdicts require explicit user confirmation.
7. **PAPER** — the strongest deployment this skill may recommend is paper
   trading. Live execution is a user decision outside this skill's authority.

## Archetype discipline

Name the archetype (`momentum`, `mean_reversion`, `multi_factor`,
`pairs_trading`, `technical`, `ml_enhanced`, `event_driven`, `value`) and stay
inside its logic. "Momentum with 12 confirming indicators" is not momentum —
it is 12 extra parameters begging the overfit preflight to fail.

## Counting variants (the honesty ledger)

Every parameter combination tried, universe swapped, or date range adjusted
increments `variants_tried`. The number follows the strategy to
backtest-validation's Deflated Sharpe Ratio. Understating it does not improve
the strategy; it just moves the lie downstream where the DSR will price it.

## Guardrails

- No code before the spec passes gate 1.
- No performance claims before gate 2; no "expected returns" from thin air.
- Forbidden claims ("guaranteed", "risk-free", "稳赚", "保证收益") fail the
  spec mechanically — the validator scans every string field.
- Position sizing "all-in" or absent hard risk controls fail the spec.
- Deploy advice caps at paper trading, always.
