# Inventory policy — formulas and thresholds

| Quantity | Formula | Notes |
|---|---|---|
| z | Φ⁻¹(service level) | 95% → 1.645, 98% → 2.054 |
| Safety stock | z · √(L·σ_d² + d̄²·σ_L²) | d̄, σ_d: mean and sample std of daily demand; L, σ_L: lead time mean and std (days) |
| Reorder point | d̄·L + safety stock | |
| Order-up-to | reorder point + d̄·R | R = review period in days |
| Inventory position | on hand + on order − backordered | |
| Order quantity | order-up-to − position | only when position ≤ reorder point |
| Days of cover | on hand / d̄ | |

Safety stock, reorder point and quantities are rounded **up**: a fractional unit
cannot be held, and rounding the buffer down quietly lowers the service level.

**Why σ_L matters.** With d̄ = 15, σ_d = 5.19, L = 4: σ_L = 0 gives safety stock
18; σ_L = 1 day gives 31. Lead-time spread usually dominates for fast movers.

**No policy under 14 days of history.** A standard deviation from a handful of
days is noise; the resulting safety stock is confidently wrong.

## Classification

- **ABC** — annual consumption value d̄·365·unit cost, ranked within one
  shipper. A while the cumulative share before the SKU is < 80%, B < 95%, else C.
- **XYZ** — coefficient of variation σ_d / d̄: X ≤ 0.5, Y ≤ 1.0, Z above.
- **Movement** — days since last movement: slow ≥ 30, dead ≥ 90.
- **Excess** — more than 180 days of cover.

## Worked reference (the script's `--demo`)

Demand 10 for 7 days then 20 for 7 days → d̄ = 15, σ_d = √(350/13) = 5.18874.
L = 4, σ_L = 0, 95%:

- safety stock = 1.644854 · √(4 · 26.92308) = 17.0696 → **18**
- reorder point = 60 + 17.0696 = 77.0696 → **78**
- order-up-to = 77.0696 + 105 = 182.0696 → **183**
- on hand 50 → order ⌈182.0696 − 50⌉ = **133**
