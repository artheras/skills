---
name: execution-position
description: >-
  Convert a trading signal into a sized, risk-gated PAPER order intent — or a
  refusal with reasons. Trigger for "这个信号该买多少", "帮我算仓位",
  "凯利公式下注多少", "现在要不要加仓", "position sizing", "how much should I
  buy", "simulate this trade", or whenever the user (1) has a signal/decision
  and asks for the size, (2) wants a trade checked against limits before
  acting, (3) asks about stops or exposure, or (4) another skill hands over a
  strategy/rebalance that needs execution shape. Fire even for casual
  "要不要梭哈". Do NOT trigger for portfolio-wide weight construction
  (portfolio-optimization) or post-hoc risk analysis (risk-assessment). NEVER
  place live orders.
---

# Execution & Position

The distance between a good signal and a good trade is sizing, limits, and
costs. This skill is the boring adult at the door: it sizes with declared
inputs, checks the hard limits, prices the friction, and emits **paper
intents only**.

## Authority boundary (read first)

The gate's output is a `paper_only: true` intent. A request for live
execution FAILS the gate mechanically — live orders are a human decision made
outside this skill, in the broker's own interface. This mirrors the platform
rule: unimplemented broker paths return errors, never fake fills.

## Sizing doctrine

- **vol_target** (default): weight = risk budget / annualized vol. Needs a
  real volatility estimate; the gate refuses to guess when none is supplied.
- **kelly**: only from a **declared** edge (win rate + payoff ratio) — the
  declaration is the user's claim and ships verbatim in the intent for audit.
  Computing an edge from sample means is prohibited here (that is
  backtest-validation's jurisdiction, and even then it is a backtest, not an
  edge). Fraction hard-capped at 0.25: full Kelly on an estimated edge
  over-bets by construction.
- **fixed_weight**: explicit user weight, still subject to every gate.

## Workflow

1. Assemble the spec (`references/order-schema.md`): order, portfolio state,
   limits, market context (vol, ADV, spread). Missing limits get conservative
   defaults; missing volatility fails vol-target sizing honestly.
2. Run `python scripts/position_gate.py SPEC.json` (or `--demo`).
3. On PASS/WARN: present the intent — side, delta weight, notional, cost
   estimate in bps — plus every warning verbatim (a `noise_stop` warning is
   more valuable than the intent itself).
4. On FAIL: the deliverable is the refusal and its reasons. Do not shrink the
   order just enough to sneak past a limit without telling the user which
   limit it was.
5. Execution of the paper intent goes to the platform's paper-trading path;
   filled paper results can then feed risk-assessment.

## Guardrails

- `paper_only` on every intent; live requests fail mechanically.
- No volatility estimate → no vol-target size. No declared edge → no Kelly.
- Kelly fraction cap 0.25 is not negotiable via prompt.
- Cost figures are labeled estimates (linear impact placeholder).
- Liquidity gate: > 10% of ADV fails; no ADV data → check skipped and said so.
