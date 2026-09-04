# Profit input schema

One JSON object: `{"stores": [...]}`. Each store carries two periods —
`current` and `prior` — with the same ten cost-bucket keys in each. A bucket
that wasn't supplied is `null`, not `0`.

```jsonc
{
  "stores": [
    {
      "name": "OZON-Store-A",
      "currency": "RUB",
      "current": {
        "revenue": 1180000,
        "cogs": 472000,
        "platform_commission": 177000,
        "advertising": 180600,
        "logistics": 94400,
        "warehousing": 30000,
        "returns": 15000,
        "refunds": 10000,
        "payment_fees": 5000,
        "penalties": 3000,
        "fx_impact": 0,
        "tax": 7000
      },
      "prior": {
        "revenue": 1000000,
        "cogs": 400000,
        "platform_commission": 150000,
        "advertising": 100000,
        "logistics": 80000,
        "warehousing": 30000,
        "returns": 15000,
        "refunds": 10000,
        "payment_fees": 5000,
        "penalties": 3000,
        "fx_impact": 0,
        "tax": 7000
      }
    }
  ]
}
```

## The ten cost buckets

| Bucket | What it captures |
|---|---|
| `cogs` | Landed cost of the units actually sold this period |
| `platform_commission` | Marketplace's take-rate on the sale |
| `advertising` | Ad spend attributable to the store/period |
| `logistics` | Outbound freight/last-mile, this period's shipments |
| `warehousing` | Storage fees for the period, including long-term-storage surcharges |
| `returns` | Value of returned inventory (lost sale, not always lost margin — see note) |
| `refunds` | Cash refunded to customers, distinct from `returns` (a refund without a physical return is possible; a return with only partial refund is too) |
| `payment_fees` | Payment-processor/gateway fees |
| `penalties` | Marketplace penalties/fines (late shipment, listing violations, etc.) |
| `fx_impact` | Gain/loss from currency conversion, if revenue and costs are denominated differently — `0` is a real, valid value here, not a missing one |
| `tax` | VAT/sales tax borne by the seller (not tax collected on behalf of the platform and remitted, which nets out) |

## Why `null` and `0` are not interchangeable

Every one of these buckets, left out, makes the reported profit look
**better**, never worse — that's the reason the gate treats a missing bucket
as a hard "can't compute a real number" rather than a soft "assume it's
small." `fx_impact` is the one bucket where `0` is a common, entirely valid
real value (single-currency operations genuinely have no FX impact) — the
schema still requires it be stated explicitly rather than defaulted, so a
seller who *should* have an FX exposure doesn't get it silently assumed away.
