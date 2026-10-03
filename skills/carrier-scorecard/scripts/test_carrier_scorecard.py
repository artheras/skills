"""Hand-computed reference values and shipper isolation for carrier_scorecard.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import carrier_scorecard as cs

HERE = Path(__file__).parent


def test_wilson_reference_values():
    assert round(cs.wilson_lower_bound(1, 1), 4) == 0.2065
    assert round(cs.wilson_lower_bound(98, 100), 4) == 0.9300
    assert cs.wilson_lower_bound(98, 100) > cs.wilson_lower_bound(1, 1)


def test_ranking_uses_the_lower_bound():
    board = cs.score(cs._waybills("LUCKY", 20, 20, 6.0) + cs._waybills("STEADY", 100, 95, 5.0))["scorecard"]
    assert {b["carrier"]: b["rank_in_lane"] for b in board} == {"STEADY": 1, "LUCKY": 2}


def test_reference_saving():
    savings = cs.score(cs._waybills("PRICEY", 30, 27, 8.0) + cs._waybills("CHEAP", 30, 29, 5.0))["savings"]
    assert [(s["from_carrier"], s["to_carrier"], s["estimated_saving"]) for s in savings] == [("PRICEY", "CHEAP", 900.0)]


def test_cheaper_but_less_reliable_is_not_suggested():
    assert cs.score(cs._waybills("RELIABLE", 30, 30, 8.0) + cs._waybills("FLAKY", 30, 15, 5.0))["savings"] == []


def test_overcharge_on_a_contracted_lane():
    lane = cs._waybills("X", 9, 9, 5.0)
    lane[0]["total_cost"], lane[1]["total_cost"] = 52.0, 48.0
    lane.append({"carrier": "X", "origin": "SH", "destination": "BJ", "total_cost": 300,
                 "billed_weight_kg": 10, "waybill_no": "OUTLIER"})
    flagged = [a["waybill_no"] for a in cs.score(lane)["anomalies"] if a["kind"] == "cost_per_kg"]
    assert flagged == ["OUTLIER"]


def test_identical_rates_flag_nothing():
    assert [a for a in cs.score(cs._waybills("X", 10, 10, 5.0))["anomalies"] if a["kind"] == "cost_per_kg"] == []


def test_mixed_shippers_are_refused_without_naming_them():
    records = [{"owner_id": "ACME", "carrier": "X", "total_cost": 10},
               {"owner_id": "GLOBEX", "carrier": "SECRET", "total_cost": 999}]
    with pytest.raises(cs.InputError) as caught:
        cs.score(records)
    assert "GLOBEX" not in str(caught.value)
    scoped = json.dumps(cs.score(records, owner="ACME"))
    assert "GLOBEX" not in scoped and "SECRET" not in scoped and "999" not in scoped


def test_demo_passes():
    result = subprocess.run([sys.executable, str(HERE / "carrier_scorecard.py"), "--demo"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
