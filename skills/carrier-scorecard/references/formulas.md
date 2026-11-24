# Carrier scorecard — formulas and thresholds

## Ranking

Within each lane (origin → destination), carriers with at least `--min-shipments`
(default 20) are ranked by the Wilson lower bound of their on-time rate, then by
median cost per kg:

    lower = (p̂ + z²/2n − z·√(p̂(1−p̂)/n + z²/4n²)) / (1 + z²/n),   z = 1.96 at 95%

| On time | Raw rate | Lower bound |
|---|---|---|
| 1 / 1 | 100% | 20.7% |
| 20 / 20 | 100% | 83.9% |
| 95 / 100 | 95% | 88.8% |
| 98 / 100 | 98% | 93.0% |

So a short perfect record does not outrank a long, slightly imperfect one.

## Anomalies

- **Cost per kg**, within a lane with at least 5 weighed shipments: modified
  z-score Mᵢ = 0.6745·(xᵢ − median)/MAD > 3.5 (Iglewicz & Hoaglin). When MAD is
  0 — usual on a contracted lane, where most shipments share one rate — use
  Mᵢ = (xᵢ − median)/(1.253314·MeanAD). Only the expensive side is flagged.
- **Weight**: billed weight > 1.2 × actual weight. Check dimensional weight
  before disputing.

Billed weight is used for cost per kg where present, otherwise actual weight.

## Savings

For each ranked carrier on a lane, the best alternative that is cheaper per kg
and has a lower bound at least as high:

    estimate = carrier's kg on the lane × (its median cost/kg − alternative's)

Not modelled: contract terms, surcharges, minimum charges, capacity, and whether
the alternative's rate holds at the higher volume.

## Worked reference (the script's `--demo`)

PRICEY: 30 shipments × 10 kg at 8/kg, 27/30 on time. CHEAP: 30 at 5/kg, 29/30.
CHEAP's lower bound is higher, so the saving is 300 kg × (8 − 5) = **900**, and
nothing is suggested in the other direction.
