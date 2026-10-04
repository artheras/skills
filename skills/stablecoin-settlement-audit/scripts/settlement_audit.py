#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
settlement_audit.py — reconcile freight invoices against on-chain stablecoin payments.

Standard library only. Read-only: it never needs, asks for, or accepts a private
key or seed phrase. Payments are read from a file you export, or — only with
--rpc — from a Solana JSON-RPC endpoint.

Every amount is an integer count of the token's smallest unit (USDC: 6 decimals,
so 1.25 USDC = 1_250_000). Floats are never used for money; an amount with more
decimals than the token has is an input error, not something to round.

Matching, in this order:
  1. Reference. A transfer whose memo contains an invoice id as a whole token is
     that invoice's payment. References are resolved against ALL invoices before
     anything is scoped to a shipper, so another shipper's payment can never be
     taken for this one's. Paid to an address other than the invoice's payee →
     `wrong_payee`, and it does not count as payment: that is the signature of
     an address-substitution fraud. A memo naming two invoices is `ambiguous`.
  2. Amount. A transfer with no reference is matched only if exactly one open
     invoice has the same payee and exactly the same amount; it is marked
     `matched_by_amount` (lower confidence). If an invoice with that payee and
     amount is already paid, it is a `possible_duplicate`. Otherwise unmatched.

Per invoice: paid, underpaid, overpaid (duplicate_payment when two or more
transfers each cover the full amount), or unpaid; overdue when not fully paid
and past due_date.

Shipper isolation as in the other logistics skills: invoices spanning shippers
are refused unless --owner or --all-owners is given, refusals never name other
shippers, and a single shipper's report leaves out transfers it cannot
attribute to that shipper's invoices.

Usage:
    python settlement_audit.py --invoices invoices.csv --transfers transfers.csv --owner ACME
    python settlement_audit.py --invoices invoices.csv --rpc https://api.mainnet-beta.solana.com
    python settlement_audit.py --demo
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import ssl
import sys
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC on Solana mainnet
USDC_DECIMALS = 6
INTERNAL = "INTERNAL — cross-shipper view; not for client distribution"
_BASE58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

SEVERITY = ["wrong_payee", "duplicate_payment", "possible_duplicate", "overpaid", "underpaid_overdue",
            "unpaid_overdue", "ambiguous", "matched_by_amount", "underpaid"]


class InputError(ValueError):
    pass


# ── Input ────────────────────────────────────────────────────────────────────

def to_units(value, decimals: int, where: str) -> int:
    """'1.25' → 1250000 for 6 decimals; refuses anything that would need rounding."""
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, AttributeError):
        raise InputError(f"{where}: {value!r} is not an amount") from None
    units = amount * (10 ** decimals)
    if units != units.to_integral_value():
        raise InputError(f"{where}: {value} has more than {decimals} decimals")
    if units < 0:
        raise InputError(f"{where}: negative amount")
    return int(units)


def from_units(units: int, decimals: int) -> str:
    sign = "-" if units < 0 else ""
    whole, frac = divmod(abs(units), 10 ** decimals)
    return f"{sign}{whole}.{frac:0{decimals}d}".rstrip("0").rstrip(".") if decimals else f"{sign}{whole}"


def _field(rec: dict, *names: str) -> str:
    for name in names:
        value = rec.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _wallet(value: str, where: str) -> str:
    if not _BASE58.match(value or ""):
        # A mistyped payee is exactly what lets a payment go astray unnoticed.
        raise InputError(f"{where}: {value!r} is not a Solana address")
    return value


def _date(value: str, where: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        raise InputError(f"{where}: due_date {value!r} is not YYYY-MM-DD") from None


def load(path: Path, key: str):
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get(key) if isinstance(data, dict) else data
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def scope(records, owner=None, all_owners=False):
    labelled = [r for r in records if _field(r, "owner_id")]
    if not labelled:
        if owner:
            raise InputError(f"owner {owner!r} requested, but the invoices carry no owner_id")
        return records, {"mode": "single_tenant", "client_facing": True}
    if len(labelled) != len(records):
        raise InputError("some invoices have no owner_id and cannot be attributed to a shipper")
    owners = {_field(r, "owner_id") for r in labelled}
    if owner:
        picked = [r for r in labelled if _field(r, "owner_id") == owner]
        if not picked:
            raise InputError(f"No invoices for owner {owner!r}")
        return picked, {"mode": "single_owner", "owner_id": owner, "client_facing": True}
    if len(owners) == 1:
        return labelled, {"mode": "single_owner", "owner_id": next(iter(owners)), "client_facing": True}
    if all_owners:
        return labelled, {"mode": "all_owners", "shipper_count": len(owners), "client_facing": False,
                          "marker": INTERNAL}
    raise InputError(f"These invoices belong to {len(owners)} different shippers. "
                     f"Pass --owner for one shipper, or --all-owners for the internal view.")


def _invoices(records, decimals):
    out = {}
    for row, rec in enumerate(records, 1):
        iid = _field(rec, "invoice_id")
        if not iid:
            raise InputError(f"invoice row {row}: invoice_id is required")
        if iid in out:
            raise InputError(f"invoice {iid} appears twice")
        currency = _field(rec, "currency").upper()
        if currency and currency not in ("USD", "USDC"):
            raise InputError(f"invoice {iid}: currency {currency} is not settled in USDC")
        out[iid] = {
            "invoice_id": iid,
            "owner_id": _field(rec, "owner_id"),
            "carrier": _field(rec, "carrier"),
            "payee": _wallet(_field(rec, "payee_wallet"), f"invoice {iid}"),
            "units": to_units(_field(rec, "amount"), decimals, f"invoice {iid}"),
            "due": _date(_field(rec, "due_date"), f"invoice {iid}"),
        }
    return out


def _transfers(records, mint, decimals):
    seen, out, other_mint = set(), [], 0
    for row, rec in enumerate(records, 1):
        sig = _field(rec, "signature")
        if not sig:
            raise InputError(f"transfer row {row}: signature is required")
        if _field(rec, "mint") and _field(rec, "mint") != mint:
            other_mint += 1
            continue
        if sig in seen:      # the same transaction exported twice is one payment
            continue
        seen.add(sig)
        raw = _field(rec, "amount_raw")
        units = int(raw) if raw else to_units(_field(rec, "amount"), decimals, f"transfer {sig[:12]}")
        out.append({
            "signature": sig,
            "to": _wallet(_field(rec, "to_owner", "to", "recipient"), f"transfer {sig[:12]}"),
            "from": _field(rec, "from_owner", "from", "sender"),
            "units": units,
            "memo": _field(rec, "memo"),
            "block_time": _field(rec, "block_time"),
        })
    out.sort(key=lambda t: (str(t["block_time"]), t["signature"]))
    return out, other_mint


def _references(memo: str, invoice_ids) -> list:
    if not memo:
        return []
    return [iid for iid in invoice_ids
            if re.search(rf"(?<![A-Za-z0-9_\-]){re.escape(iid)}(?![A-Za-z0-9_\-])", memo)]


# ── Audit ────────────────────────────────────────────────────────────────────

def audit(invoice_records, transfer_records, owner=None, all_owners=False, as_of=None,
          mint=USDC_MINT, decimals=USDC_DECIMALS):
    reported, scope_info = scope(invoice_records, owner, all_owners)
    everything = _invoices(invoice_records, decimals)     # matching sees every invoice
    in_scope = {_field(r, "invoice_id") for r in reported}
    transfers, other_mint = _transfers(transfer_records, mint, decimals)
    as_of = as_of or date.today()
    fmt = lambda u: from_units(u, decimals)  # noqa: E731

    # A report for one shipper (as opposed to the 3PL's own --all-owners view)
    # must not list transfers it cannot tie to that shipper's invoices.
    client_facing_owner = (not all_owners and scope_info["mode"] == "single_owner"
                           and any(i["owner_id"] for i in everything.values()))
    claims = defaultdict(list)      # invoice_id → [(transfer, how)]
    exceptions, unmatched, withheld = [], [], 0

    def note(kind, invoice_ids, transfer=None, **extra):
        shown = [i for i in invoice_ids if i in in_scope]
        if invoice_ids and not shown:
            return False   # someone else's business
        item = {"kind": kind, "invoice_ids": shown, **extra}
        if transfer:
            item.update(signature=transfer["signature"], amount=fmt(transfer["units"]), paid_to=transfer["to"])
        exceptions.append(item)
        return True

    pending = []
    for t in transfers:
        refs = _references(t["memo"], everything)
        if len(refs) > 1:
            note("ambiguous", refs, t, detail="memo names more than one invoice")
        elif refs:
            invoice = everything[refs[0]]
            if t["to"] != invoice["payee"]:
                note("wrong_payee", refs, t, expected_payee=invoice["payee"],
                     detail="paid to an address that is not this invoice's payee; does not count as payment")
            else:
                claims[refs[0]].append((t, "reference"))
        else:
            pending.append(t)

    for t in pending:
        open_ = [i for i in everything.values()
                 if i["payee"] == t["to"] and i["units"] == t["units"] and not claims[i["invoice_id"]]]
        if len(open_) == 1:
            claims[open_[0]["invoice_id"]].append((t, "amount"))
            continue
        if len(open_) > 1:
            note("ambiguous", [i["invoice_id"] for i in open_], t,
                 detail="no reference, and several open invoices have this payee and amount")
            continue
        settled = [i["invoice_id"] for i in everything.values()
                   if i["payee"] == t["to"] and i["units"] == t["units"]]
        if settled and note("possible_duplicate", settled, t,
                            detail="no reference; an invoice with this payee and amount is already paid"):
            continue
        if client_facing_owner:
            withheld += 1   # cannot be attributed to this shipper; not theirs to see
        else:
            unmatched.append({"signature": t["signature"], "amount": fmt(t["units"]), "paid_to": t["to"],
                              "memo": t["memo"]})

    rows, totals = [], defaultdict(int)
    for iid in sorted(in_scope):
        inv = everything[iid]
        paid = sum(t["units"] for t, _ in claims[iid])
        status = ("unpaid" if paid == 0 else "underpaid" if paid < inv["units"]
                  else "paid" if paid == inv["units"] else "overpaid")
        overdue = status in ("unpaid", "underpaid") and inv["due"] is not None and inv["due"] < as_of
        by_amount = any(how == "amount" for _, how in claims[iid])
        full_hits = sum(1 for t, _ in claims[iid] if t["units"] == inv["units"])
        rows.append({
            "invoice_id": iid, "carrier": inv["carrier"], "payee": inv["payee"],
            "amount": fmt(inv["units"]), "paid": fmt(paid), "status": status, "overdue": overdue,
            "due_date": inv["due"].isoformat() if inv["due"] else None,
            "payments": [{"signature": t["signature"], "amount": fmt(t["units"]), "matched_by": how}
                         for t, how in claims[iid]],
        })
        if status == "overpaid":
            kind = "duplicate_payment" if full_hits >= 2 else "overpaid"
            note(kind, [iid], excess=fmt(paid - inv["units"]))
            totals["overpaid"] += paid - inv["units"]
        if status == "underpaid":
            note("underpaid_overdue" if overdue else "underpaid", [iid], shortfall=fmt(inv["units"] - paid))
            totals["shortfall"] += inv["units"] - paid
        if status == "unpaid" and overdue:
            note("unpaid_overdue", [iid], amount=fmt(inv["units"]), due_date=inv["due"].isoformat())
            totals["unpaid_overdue"] += inv["units"]
        if by_amount:
            note("matched_by_amount", [iid], detail="paid without a reference; matched on payee and exact amount")
    totals["wrong_payee"] = sum(to_units(e["amount"], decimals, "") for e in exceptions if e["kind"] == "wrong_payee")

    exceptions.sort(key=lambda e: (SEVERITY.index(e["kind"]), e["invoice_ids"]))
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
    return {
        "scope": scope_info,
        "as_of": as_of.isoformat(),
        "summary": {
            "invoices": len(rows), **dict(counts),
            "overdue": sum(r["overdue"] for r in rows),
            "exceptions": len(exceptions),
            "overpaid_total": fmt(totals["overpaid"]),
            "underpaid_shortfall": fmt(totals["shortfall"]),
            "unpaid_overdue_total": fmt(totals["unpaid_overdue"]),
            "paid_to_wrong_address": fmt(totals["wrong_payee"]),
        },
        "exceptions": exceptions,
        "invoices": rows,
        "unmatched_transfers": unmatched,
        "assumptions": [
            f"token mint {mint}, {decimals} decimals; amounts compared exactly in the smallest unit",
            "a memo matches an invoice id only as a whole token (INV-1 does not match INV-10)",
            "references are resolved against all invoices before scoping to a shipper",
            "an amount-only match is lower confidence and is listed as an exception to confirm",
            f"{other_mint} transfer(s) in another token ignored",
            f"{withheld} transfer(s) not attributable to this shipper's invoices left out of a client-facing report"
            if withheld else "no transfers withheld",
            "read-only: no private key or seed phrase is needed or accepted",
        ],
    }


# ── Reading the chain (only with --rpc) ──────────────────────────────────────

def transfers_from_parsed_tx(tx: dict, mint: str) -> list:
    """Token movements of `mint` in one getTransaction(jsonParsed) result."""
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return []   # a failed transaction moved nothing
    message = ((tx.get("transaction") or {}).get("message")) or {}
    instructions = list(message.get("instructions") or [])
    for inner in meta.get("innerInstructions") or []:
        instructions += inner.get("instructions") or []
    memo = " ".join(str(i.get("parsed")) for i in instructions
                    if i.get("program") == "spl-memo" and i.get("parsed"))

    def by_owner(balances):
        totals = defaultdict(int)
        for b in balances or []:
            if b.get("mint") == mint and b.get("owner"):
                totals[b["owner"]] += int((b.get("uiTokenAmount") or {}).get("amount") or 0)
        return totals

    pre, post = by_owner(meta.get("preTokenBalances")), by_owner(meta.get("postTokenBalances"))
    deltas = {o: post.get(o, 0) - pre.get(o, 0) for o in set(pre) | set(post)}
    senders = [o for o, d in deltas.items() if d < 0]
    signature = ((tx.get("transaction") or {}).get("signatures") or [""])[0]
    block_time = tx.get("blockTime")
    when = datetime.fromtimestamp(block_time, tz=timezone.utc).isoformat() if block_time else ""
    return [{"signature": signature, "to_owner": owner, "from_owner": senders[0] if len(senders) == 1 else "",
             "amount_raw": str(delta), "mint": mint, "memo": memo, "block_time": when}
            for owner, delta in sorted(deltas.items()) if delta > 0]


def _tls_context():
    """Verified TLS. python.org's macOS Python ships without root certificates
    until "Install Certificates" is run; certifi's bundle is used when present.
    Verification is never turned off."""
    try:
        import certifi  # optional
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _rpc(url: str, method: str, params: list):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30, context=_tls_context()) as response:
        reply = json.loads(response.read())
    if "error" in reply:
        raise InputError(f"RPC {method}: {reply['error']}")
    return reply["result"]


# Transaction V1 reached mainnet in September 2026; asking for version 0 makes
# the node refuse every V1 transaction.
MAX_TX_VERSION = 1


def fetch_transfers(url: str, payees, mint=USDC_MINT, limit=100, rpc=_rpc, unreadable=None) -> list:
    """Incoming `mint` transfers to each payee wallet. Reads only; signs nothing.

    A transaction the node will not return is recorded in `unreadable`, never
    skipped quietly: a payment that is missing from the data would otherwise
    turn a paid invoice into an "unpaid" one.
    """
    unreadable = unreadable if unreadable is not None else []
    if not (url.startswith("https://") or url.startswith("http://localhost") or url.startswith("http://127.0.0.1")):
        raise InputError("--rpc must be an https URL (or a local node)")
    found = []
    for payee in sorted(set(payees)):
        accounts = rpc(url, "getTokenAccountsByOwner", [payee, {"mint": mint}, {"encoding": "jsonParsed"}])
        for account in (accounts or {}).get("value", []):
            for entry in rpc(url, "getSignaturesForAddress", [account["pubkey"], {"limit": limit}]) or []:
                if entry.get("err") is not None:
                    continue
                try:
                    tx = rpc(url, "getTransaction", [entry["signature"], {
                        "encoding": "jsonParsed", "maxSupportedTransactionVersion": MAX_TX_VERSION}])
                except (InputError, OSError) as exc:
                    unreadable.append({"signature": entry["signature"], "error": str(exc)[:200]})
                    continue
                if not tx:
                    unreadable.append({"signature": entry["signature"], "error": "not returned"})
                    continue
                found += [t for t in transfers_from_parsed_tx(tx, mint) if t["to_owner"] == payee]
    return found


# ── Demo ─────────────────────────────────────────────────────────────────────

def _addr(name: str) -> str:
    return (name + "1" * 44)[:44]


DEMO_INVOICES = [
    {"invoice_id": "INV-1", "owner_id": "ACME", "carrier": "SF", "payee_wallet": _addr("SFcarrier"), "amount": "1250.00", "due_date": "2026-09-30"},
    {"invoice_id": "INV-2", "owner_id": "ACME", "carrier": "SF", "payee_wallet": _addr("SFcarrier"), "amount": "800.00", "due_date": "2026-09-20"},
    {"invoice_id": "INV-3", "owner_id": "ACME", "carrier": "JD", "payee_wallet": _addr("JDcarrier"), "amount": "640.50", "due_date": "2026-10-10"},
    {"invoice_id": "INV-4", "owner_id": "ACME", "carrier": "JD", "payee_wallet": _addr("JDcarrier"), "amount": "300.00", "due_date": "2026-09-25"},
    {"invoice_id": "INV-5", "owner_id": "ACME", "carrier": "YTO", "payee_wallet": _addr("YTcarrier"), "amount": "99.99", "due_date": "2026-10-15"},
    {"invoice_id": "INV-6", "owner_id": "ACME", "carrier": "YTO", "payee_wallet": _addr("YTcarrier"), "amount": "450.00", "due_date": "2026-09-01"},
]
DEMO_TRANSFERS = [
    {"signature": "sig1", "to_owner": _addr("SFcarrier"), "amount": "1250.00", "memo": "INV-1", "block_time": "2026-09-28"},
    {"signature": "sig2", "to_owner": _addr("SFcarrier"), "amount": "500.00", "memo": "INV-2 partial", "block_time": "2026-09-19"},
    {"signature": "sig3", "to_owner": _addr("JDcarrier"), "amount": "640.50", "memo": "INV-3", "block_time": "2026-10-01"},
    {"signature": "sig4", "to_owner": _addr("JDcarrier"), "amount": "640.50", "memo": "INV-3", "block_time": "2026-10-02"},
    {"signature": "sig5", "to_owner": _addr("Attacker"), "amount": "300.00", "memo": "INV-4", "block_time": "2026-09-24"},
    {"signature": "sig6", "to_owner": _addr("YTcarrier"), "amount": "99.99", "memo": "", "block_time": "2026-10-03"},
    {"signature": "sig7", "to_owner": _addr("SFcarrier"), "amount": "75.00", "memo": "", "block_time": "2026-10-03"},
    {"signature": "sig8", "to_owner": _addr("SFcarrier"), "amount": "75.00", "memo": "", "mint": "OtherToken", "block_time": "2026-10-03"},
]


def demo() -> int:
    """Hand-computed reference values, as of 2026-10-04:
      INV-1 paid; INV-2 500 of 800 → shortfall 300, overdue; INV-3 paid twice → duplicate, excess 640.5;
      INV-4 paid to the wrong address → 300 to wrong payee, invoice still unpaid and overdue;
      INV-5 paid without a reference → matched by amount; INV-6 unpaid, overdue.
      Unpaid overdue = 300 + 450 = 750. sig8 is another token and is ignored.
      sig7 matches nothing. In this client-facing report it is withheld, not listed:
      a 3PL pays many shippers' carriers from one wallet, so a transfer that is not
      this shipper's could be another's. The internal --all-owners view lists it.
    """
    result = audit(DEMO_INVOICES, DEMO_TRANSFERS, as_of=date(2026, 10, 4))
    status = {r["invoice_id"]: (r["status"], r["overdue"]) for r in result["invoices"]}
    expected = {"INV-1": ("paid", False), "INV-2": ("underpaid", True), "INV-3": ("overpaid", False),
                "INV-4": ("unpaid", True), "INV-5": ("paid", False), "INV-6": ("unpaid", True)}
    summary = result["summary"]
    failures = []
    if status != expected:
        failures.append(f"statuses {status}")
    if (summary["overpaid_total"], summary["underpaid_shortfall"], summary["unpaid_overdue_total"],
            summary["paid_to_wrong_address"]) != ("640.5", "300", "750", "300"):
        failures.append(f"totals {summary}")
    if result["exceptions"][0]["kind"] != "wrong_payee":
        failures.append("the wrong-payee payment must be the first exception")
    if result["unmatched_transfers"] or "1 transfer(s) not attributable" not in " ".join(result["assumptions"]):
        failures.append("an unattributable transfer must be withheld from a client-facing report")
    internal = audit(DEMO_INVOICES, DEMO_TRANSFERS, all_owners=True, as_of=date(2026, 10, 4))
    if [t["signature"] for t in internal["unmatched_transfers"]] != ["sig7"]:
        failures.append("the internal view lists unmatched transfers")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        print("DEMO MISMATCH: " + "; ".join(failures), file=sys.stderr)
        return 1
    print("demo: reference values verified", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Reconcile freight invoices against stablecoin payments")
    ap.add_argument("--invoices", type=Path, help="CSV or JSON of invoices")
    ap.add_argument("--transfers", type=Path, help="CSV or JSON of exported transfers")
    ap.add_argument("--rpc", help="read transfers from this Solana JSON-RPC URL instead")
    ap.add_argument("--limit", type=int, default=100, help="signatures to read per token account (with --rpc)")
    ap.add_argument("--owner", help="shipper (owner_id) to report on")
    ap.add_argument("--all-owners", action="store_true", help="internal cross-shipper view")
    ap.add_argument("--as-of", help="date for overdue checks (YYYY-MM-DD, default today)")
    ap.add_argument("--mint", default=USDC_MINT)
    ap.add_argument("--decimals", type=int, default=USDC_DECIMALS)
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args(argv)
    if args.demo:
        return demo()
    if not args.invoices or not (args.transfers or args.rpc):
        ap.error("--invoices and one of --transfers / --rpc are required (or use --demo)")
    try:
        invoices = load(args.invoices, "invoices") or []
        unreadable = []
        if args.rpc:
            payees = [_field(r, "payee_wallet") for r in invoices]
            transfers = fetch_transfers(args.rpc, payees, args.mint, args.limit, unreadable=unreadable)
        else:
            transfers = load(args.transfers, "transfers") or []
        as_of = date.fromisoformat(args.as_of) if args.as_of else None
        result = audit(invoices, transfers, args.owner, args.all_owners, as_of, args.mint, args.decimals)
        if unreadable:
            # The result is not trustworthy as "unpaid" while payments may be missing.
            result["incomplete"] = {"unreadable_transactions": len(unreadable), "examples": unreadable[:5],
                                    "note": "some transactions could not be read; an invoice shown as unpaid "
                                            "may have been paid in one of them"}
            print(f"warning: {len(unreadable)} transaction(s) could not be read; see 'incomplete'",
                  file=sys.stderr)
    except (InputError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
