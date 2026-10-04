"""Each rule of the settlement audit, and each way a reconciliation goes wrong.

Money moves on these answers, so every test is a specific mistake: a payment
credited to the wrong invoice, to another shipper's invoice, or not at all;
a stolen payment counted as paid; a rounding that hides a cent.
"""

from datetime import date

import pytest

import settlement_audit as sa
from settlement_audit import InputError, audit

AS_OF = date(2026, 10, 4)


def addr(name):
    return sa._addr(name)


def inv(iid, amount, payee="Carrier", owner="ACME", due="2026-10-30"):
    return {"invoice_id": iid, "owner_id": owner, "payee_wallet": addr(payee), "amount": amount, "due_date": due}


def tx(sig, amount, to="Carrier", memo="", **kw):
    return {"signature": sig, "to_owner": addr(to), "amount": amount, "memo": memo, **kw}


def run(invoices, transfers, **kw):
    kw.setdefault("as_of", AS_OF)
    return audit(invoices, transfers, **kw)


def status(result):
    return {r["invoice_id"]: r["status"] for r in result["invoices"]}


def kinds(result):
    return [e["kind"] for e in result["exceptions"]]


class TestMoney:
    def test_amounts_are_exact_integers_of_the_smallest_unit(self):
        assert sa.to_units("1.25", 6, "x") == 1_250_000
        assert sa.to_units("0.000001", 6, "x") == 1
        assert sa.from_units(640_500_000, 6) == "640.5"

    def test_more_decimals_than_the_token_has_is_an_error_not_a_rounding(self):
        with pytest.raises(InputError):
            sa.to_units("1.0000001", 6, "x")

    def test_a_cent_short_is_underpaid(self):
        result = run([inv("A", "100.00")], [tx("s", "99.99", memo="A")])
        assert status(result) == {"A": "underpaid"}
        assert result["summary"]["underpaid_shortfall"] == "0.01"

    def test_a_mistyped_payee_address_is_refused(self):
        with pytest.raises(InputError):
            run([{"invoice_id": "A", "payee_wallet": "0xNotAnAddress", "amount": "1"}], [])


class TestMatching:
    def test_a_reference_pays_its_invoice(self):
        assert status(run([inv("A", "10")], [tx("s", "10", memo="pay A thanks")])) == {"A": "paid"}

    def test_a_reference_is_a_whole_token(self):
        result = run([inv("INV-1", "10"), inv("INV-10", "10", payee="Second")],
                     [tx("s", "10", to="Second", memo="INV-10")])
        assert status(result) == {"INV-1": "unpaid", "INV-10": "paid"}

    def test_paid_to_the_wrong_address_is_not_payment(self):
        result = run([inv("A", "300", due="2026-09-25")], [tx("s", "300", to="Attacker", memo="A")])
        assert status(result) == {"A": "unpaid"}
        assert kinds(result)[0] == "wrong_payee"
        assert result["summary"]["paid_to_wrong_address"] == "300"

    def test_a_memo_naming_two_invoices_is_not_guessed(self):
        result = run([inv("A", "10"), inv("B", "10")], [tx("s", "10", memo="A B")])
        assert status(result) == {"A": "unpaid", "B": "unpaid"} and "ambiguous" in kinds(result)

    def test_no_reference_matches_on_one_exact_payee_and_amount(self):
        result = run([inv("A", "99.99")], [tx("s", "99.99")])
        assert status(result) == {"A": "paid"} and "matched_by_amount" in kinds(result)

    def test_no_reference_and_two_candidates_is_not_guessed(self):
        result = run([inv("A", "50"), inv("B", "50")], [tx("s", "50")])
        assert status(result) == {"A": "unpaid", "B": "unpaid"} and "ambiguous" in kinds(result)

    def test_the_same_payment_twice(self):
        result = run([inv("A", "640.50")], [tx("s1", "640.50", memo="A"), tx("s2", "640.50", memo="A")])
        assert kinds(result)[0] == "duplicate_payment"
        assert result["summary"]["overpaid_total"] == "640.5"

    def test_an_unreferenced_repeat_of_a_paid_invoice_is_a_possible_duplicate(self):
        result = run([inv("A", "75")], [tx("s1", "75", memo="A"), tx("s2", "75")])
        assert "possible_duplicate" in kinds(result)

    def test_overdue_only_when_not_fully_paid_and_past_due(self):
        result = run([inv("A", "10", due="2026-09-01"), inv("B", "10", due="2026-09-01")],
                     [tx("s", "10", memo="B")])
        rows = {r["invoice_id"]: r["overdue"] for r in result["invoices"]}
        assert rows == {"A": True, "B": False}

    def test_another_token_and_a_repeated_export_are_not_payments(self):
        result = run([inv("A", "20")], [tx("s1", "10", memo="A"), tx("s1", "10", memo="A"),
                                        tx("s2", "10", memo="A", mint="SomeOtherToken")])
        assert status(result) == {"A": "underpaid"}


class TestShipperIsolation:
    def test_mixed_shippers_are_refused_without_naming_them(self):
        with pytest.raises(InputError) as err:
            run([inv("A", "1", owner="ACME"), inv("B", "1", owner="BETA")], [])
        assert "ACME" not in str(err.value) and "BETA" not in str(err.value)

    def test_another_shippers_payment_is_never_taken_for_this_ones(self):
        # BETA's invoice B-1 is paid by reference. ACME's A-1 has the same payee
        # and amount. Scoping first and matching after would credit BETA's
        # payment to ACME by amount and report A-1 as paid.
        invoices = [inv("A-1", "500", owner="ACME"), inv("B-1", "500", owner="BETA")]
        result = run(invoices, [tx("s", "500", memo="B-1")], owner="ACME")
        assert status(result) == {"A-1": "unpaid"}
        assert "B-1" not in str(result)

    def test_a_client_report_withholds_what_it_cannot_attribute(self):
        result = run([inv("A", "10")], [tx("s", "75")], owner="ACME")
        assert result["unmatched_transfers"] == []
        assert "1 transfer(s) not attributable" in " ".join(result["assumptions"])

    def test_the_internal_view_lists_it(self):
        result = run([inv("A", "10")], [tx("s", "75")], all_owners=True)
        assert [t["signature"] for t in result["unmatched_transfers"]] == ["s"]

    def test_unlabelled_invoices_are_single_tenant(self):
        plain = {k: v for k, v in inv("A", "10").items() if k != "owner_id"}
        result = run([plain], [tx("s", "75")])
        assert [t["signature"] for t in result["unmatched_transfers"]] == ["s"]


def parsed_tx(sig, moves, memo=None, err=None, inner_memo=False, version=1):
    """A getTransaction(jsonParsed) result shaped like mainnet's.

    moves: [(owner, pre, post)] for the USDC mint.
    """
    pre = [{"accountIndex": i, "mint": sa.USDC_MINT, "owner": o, "uiTokenAmount": {"amount": str(a), "decimals": 6}}
           for i, (o, a, _) in enumerate(moves)]
    post = [{"accountIndex": i, "mint": sa.USDC_MINT, "owner": o, "uiTokenAmount": {"amount": str(b), "decimals": 6}}
            for i, (o, _, b) in enumerate(moves)]
    memo_ix = [{"program": "spl-memo", "programId": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "parsed": memo}]
    message = {"instructions": ([] if inner_memo or not memo else memo_ix)}
    meta = {"err": err, "preTokenBalances": pre, "postTokenBalances": post,
            "innerInstructions": [{"index": 0, "instructions": memo_ix}] if inner_memo and memo else []}
    return {"blockTime": 1790000000, "version": version, "meta": meta,
            "transaction": {"signatures": [sig], "message": message}}


class TestReadingTheChain:
    def test_a_transfer_with_its_memo(self):
        (t,) = sa.transfers_from_parsed_tx(
            parsed_tx("sig", [(addr("Payer"), 2_000_000, 750_000), (addr("Carrier"), 0, 1_250_000)], memo="INV-1"),
            sa.USDC_MINT)
        assert (t["to_owner"], t["from_owner"], t["amount_raw"], t["memo"]) == (
            addr("Carrier"), addr("Payer"), "1250000", "INV-1")

    def test_a_memo_in_an_inner_instruction(self):
        (t,) = sa.transfers_from_parsed_tx(
            parsed_tx("sig", [(addr("Payer"), 5, 0), (addr("Carrier"), 0, 5)], memo="INV-2", inner_memo=True),
            sa.USDC_MINT)
        assert t["memo"] == "INV-2"

    def test_a_failed_transaction_moved_nothing(self):
        assert sa.transfers_from_parsed_tx(
            parsed_tx("sig", [(addr("Payer"), 5, 0), (addr("Carrier"), 0, 5)], err={"x": 1}), sa.USDC_MINT) == []

    def test_other_tokens_are_ignored(self):
        assert sa.transfers_from_parsed_tx(
            parsed_tx("sig", [(addr("Payer"), 5, 0), (addr("Carrier"), 0, 5)]), "AnotherMint") == []

    def _fake_rpc(self, txs, refuse=()):
        calls = []

        def rpc(url, method, params):
            calls.append((method, params))
            if method == "getTokenAccountsByOwner":
                return {"value": [{"pubkey": "ata-" + params[0][:6]}]}
            if method == "getSignaturesForAddress":
                return [{"signature": s, "err": None} for s in txs]
            if params[0] in refuse:
                raise InputError("Transaction version (2) is not supported")
            return txs[params[0]]
        return rpc, calls

    def test_fetching_reads_v1_transactions(self):
        rpc, calls = self._fake_rpc({"s1": parsed_tx("s1", [(addr("P"), 9, 0), (addr("Carrier"), 0, 9)], memo="A")})
        found = sa.fetch_transfers("https://rpc.example", [addr("Carrier")], rpc=rpc)
        assert [t["signature"] for t in found] == ["s1"]
        (opts,) = [p[1] for m, p in calls if m == "getTransaction"]
        assert opts["maxSupportedTransactionVersion"] >= 1

    def test_an_unreadable_transaction_is_reported_not_skipped(self):
        rpc, _ = self._fake_rpc({"s1": None, "s2": None}, refuse={"s2"})
        unreadable = []
        sa.fetch_transfers("https://rpc.example", [addr("Carrier")], rpc=rpc, unreadable=unreadable)
        assert sorted(u["signature"] for u in unreadable) == ["s1", "s2"]

    def test_only_https_or_a_local_node(self):
        with pytest.raises(InputError):
            sa.fetch_transfers("http://rpc.example", [addr("Carrier")], rpc=lambda *a: None)


def test_the_demo_reproduces_its_reference_values():
    assert sa.demo() == 0
