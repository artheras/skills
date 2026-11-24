"""Hand-computed reference values and shipper isolation for inventory_policy.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import inventory_policy as ip

HERE = Path(__file__).parent
HISTORY = [10] * 7 + [20] * 7  # d̄ = 15, σ_d = √(350/13)


def _one(**overrides):
    record = {"sku": "A", "on_hand": 50, "lead_time_days": 4, "daily_demand": HISTORY, **overrides}
    return ip.plan([record])["items"][0]


def test_reference_values():
    a = _one()
    assert (a["safety_stock"], a["reorder_point"], a["order_up_to"], a["suggested_order_qty"]) == (18, 78, 183, 133)
    assert a["action"] == "reorder"


def test_lead_time_variability_raises_safety_stock():
    # 1.644854 · √(107.6923 + 225) = 30.0024 → 31
    assert _one(lead_time_std_days=1)["safety_stock"] == 31


def test_short_history_gets_no_policy():
    a = _one(daily_demand=[3, 4])
    assert a["action"] == "insufficient_history" and a["reorder_point"] is None


def test_abc_within_a_shipper():
    demand = [10] * 14
    items = ip.plan([
        {"sku": s, "on_hand": 100, "lead_time_days": 2, "daily_demand": demand, "unit_cost": c}
        for s, c in (("A1", 80), ("A2", 15), ("A3", 5))
    ])["items"]
    assert {i["sku"]: i["abc"] for i in items} == {"A1": "A", "A2": "B", "A3": "C"}


def test_mixed_shippers_are_refused_without_naming_them():
    records = [
        {"owner_id": "ACME", "sku": "A", "on_hand": 1, "lead_time_days": 1, "daily_demand": [1] * 14},
        {"owner_id": "GLOBEX", "sku": "B", "on_hand": 1, "lead_time_days": 1, "daily_demand": [1] * 14},
    ]
    with pytest.raises(ip.InputError) as caught:
        ip.plan(records)
    assert "GLOBEX" not in str(caught.value) and "ACME" not in str(caught.value)
    assert [i["sku"] for i in ip.plan(records, owner="ACME")["items"]] == ["A"]
    internal = ip.plan(records, all_owners=True)
    assert internal["scope"]["client_facing"] is False
    assert internal["assumptions"][0].startswith("INTERNAL")


def test_demo_passes():
    result = subprocess.run([sys.executable, str(HERE / "inventory_policy.py"), "--demo"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    json.loads(result.stdout)


def test_csv_round_trip(tmp_path):
    path = tmp_path / "skus.csv"
    path.write_text("owner_id,sku,on_hand,lead_time_days,daily_demand\n"
                    "ACME,A,50,4," + ";".join(map(str, HISTORY)) + "\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(HERE / "inventory_policy.py"), "--skus", str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["items"][0]["reorder_point"] == 78
