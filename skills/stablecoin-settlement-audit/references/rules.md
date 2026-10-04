# Settlement audit rules

All amounts are integers in the token's smallest unit. For USDC on Solana
(mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`, 6 decimals),
1.25 USDC = 1 250 000 units. Comparisons are exact.

## Which transfers count

- Only the configured mint (`--mint`, default USDC). Other tokens are counted
  in `assumptions` and ignored.
- A failed transaction moved nothing.
- The same signature twice (a repeated export) is one payment.
- From the chain, a transfer is a positive change in the payee's balance of the
  mint between `preTokenBalances` and `postTokenBalances`. The memo is every
  `spl-memo` instruction in the transaction, inner instructions included.

## Matching

1. **Reference.** An invoice id appearing in the memo as a whole token —
   `INV-1` does not match inside `INV-10`. Resolved against every invoice
   before scoping to one shipper, so another shipper's payment cannot be
   credited to this one.
   - Paid to the invoice's payee → payment.
   - Paid elsewhere → `wrong_payee`; not a payment.
   - Memo names two or more invoices → `ambiguous`; not a payment.
2. **Amount** (no reference). Exactly one open invoice with the same payee and
   identical amount → payment, flagged `matched_by_amount`. More than one →
   `ambiguous`. None open but one already settled → `possible_duplicate`.
   Otherwise unmatched.

## Invoice status

| paid vs amount | status |
|---|---|
| 0 | unpaid |
| below | underpaid (shortfall reported) |
| equal | paid |
| above | overpaid; `duplicate_payment` if two or more transfers each equal the amount |

Overdue: unpaid or underpaid, with a due date before `--as-of` (default today).

## Severity order of exceptions

wrong_payee, duplicate_payment, possible_duplicate, overpaid,
underpaid_overdue, unpaid_overdue, ambiguous, matched_by_amount, underpaid.

## Reading the chain (`--rpc`)

For each payee: `getTokenAccountsByOwner` (mint filter) → `getSignaturesForAddress`
on each token account (`--limit`, default 100) → `getTransaction` with
`jsonParsed` and `maxSupportedTransactionVersion: 1` (Transaction V1 reached
mainnet in September 2026; requesting version 0 makes the node refuse V1
transactions). A transaction that cannot be read is listed under
`incomplete`, never skipped. Only https URLs or a local node are accepted.
Nothing is signed or sent.
