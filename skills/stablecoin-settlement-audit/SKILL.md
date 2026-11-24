---
name: stablecoin-settlement-audit
description: >-
  Reconcile freight or logistics invoices against on-chain stablecoin (USDC)
  payments: which invoices are paid, short-paid, paid twice, overdue, or paid
  to an address that is not the payee. Trigger for "运费有没有付清", "USDC 对账",
  "稳定币对账", "链上付款核对", "重复付款", "付错地址", "哪些发票逾期",
  "reconcile USDC payments", "stablecoin settlement audit", "did we pay this
  invoice", "duplicate payment", "payment sent to the wrong wallet", or
  whenever the user supplies invoices with payee wallets alongside on-chain
  transfers or a wallet to check. Also for a 3PL doing this for one shipper
  (货主). Do NOT trigger for making or signing a payment, trading, token
  prices, or wallet balances alone — this skill reads and reconciles only.
---

# Stablecoin Settlement Audit

Paying carriers in USDC settles in seconds; finding out a month later that an
invoice was paid twice, short by a fee, or to a lookalike address does not.
This skill reconciles invoices against the transfers that actually landed on
chain, with the same discipline as the other logistics skills: exact
arithmetic, stated rules, one shipper at a time, and no guessing.

The matching rules do not depend on the network. Reading payments directly
from a chain (`--rpc`) currently supports USDC on Solana; for any other
network, export the transfers to a file.

## Principles

1. **Read-only, always.** Never ask for, accept, or handle a private key, seed
   phrase or wallet export. The audit needs public addresses and public
   transactions, nothing else. If the user offers a key, tell them to keep it
   and not to paste it anywhere.
2. **Exact money.** Amounts are integers in the token's smallest unit (USDC:
   6 decimals). Never round; an amount with too many decimals is an error to
   report, not to fix.
3. **A payment to the wrong address is not a payment.** A transfer that cites
   an invoice but went to an address other than the invoice's payee is
   reported first, as `wrong_payee` — the signature of address substitution —
   and the invoice stays unpaid.
4. **Reference before amount.** A memo naming the invoice is strong evidence;
   a matching amount alone is weak and is listed as `matched_by_amount` for a
   person to confirm. Two candidates means no match, never a guess.
5. **One shipper at a time.** Invoices spanning shippers are refused unless
   `--owner` or `--all-owners` is given. A client-facing report never lists
   transfers it cannot tie to that shipper's invoices; `--all-owners` output
   is marked not for client distribution.
6. **Incomplete data is said out loud.** If any transaction could not be read
   from the chain, the result carries `incomplete`: an invoice shown as unpaid
   may have been paid in it.

## Workflow — order matters

1. Get invoices: `invoice_id`, `payee_wallet`, `amount` (USD), and ideally
   `due_date`, `carrier`, `owner_id`.
2. Get payments, either an export (`signature`, `to_owner`, `amount` or
   `amount_raw`, `memo`, `mint`, `block_time`) or read them read-only:
   `python scripts/settlement_audit.py --invoices invoices.csv --rpc <https URL> --owner <shipper>`
   Without --rpc, pass `--transfers transfers.csv`.
3. Report in this order: payments to the wrong address; duplicates and
   overpayments; shortfalls and overdue invoices; then amount-only matches to
   confirm. Quote the `summary` totals and the `assumptions` block.
4. If `incomplete` is present, lead with it and do not call any invoice
   unpaid without that caveat.

## Bundled resources

- `scripts/settlement_audit.py` — the reconciliation. Standard library only
  (uses `certifi` for TLS certificates if installed). `--demo` checks
  hand-computed values: a 300 shortfall, a 640.50 duplicate, 750 unpaid and
  overdue, 300 paid to the wrong address.
- `references/rules.md` — read when the user asks why a payment was or was not
  matched, or wants different rules.
- `agents/openai.yaml` — the human-facing entry point.
