"""replenishment_plan 测试:demo 分离 + 每个分类/拒绝路径逐一验证。"""

import copy

from replenishment_plan import DEMO_INPUT, demo, plan, plan_sku


def _sku(**overrides):
    base = {
        "sku": "TEST-1",
        "current_stock": 300,
        "daily_sales_velocity": 10.0,
        "lead_time_days": 14,
        "safety_stock_days": 7,
        "on_order_qty": 0,
    }
    base.update(overrides)
    return base


def test_demo_covers_all_four_statuses():
    assert demo() == 0


def test_healthy_sku_is_ok_with_zero_suggested_order():
    row = plan_sku(_sku(current_stock=1000), review_period_days=14)
    assert row["status"] == "ok"
    assert row["suggested_order_qty"] == 0


def test_missing_velocity_is_refused_not_guessed():
    row = plan_sku(_sku(daily_sales_velocity=None), review_period_days=14)
    assert row["status"] == "velocity_unavailable"
    assert row["suggested_order_qty"] is None


def test_zero_velocity_is_also_refused():
    row = plan_sku(_sku(daily_sales_velocity=0), review_period_days=14)
    assert row["status"] == "velocity_unavailable"


def test_missing_lead_time_is_refused_not_guessed():
    row = plan_sku(_sku(lead_time_days=None), review_period_days=14)
    assert row["status"] == "lead_time_missing"
    assert row["suggested_order_qty"] is None


def test_stockout_when_no_stock_left():
    row = plan_sku(_sku(current_stock=0), review_period_days=14)
    assert row["status"] == "stockout"
    assert row["suggested_order_qty"] > 0


def test_urgent_when_cover_below_lead_time():
    # lead_time=14, velocity=10 -> urgent needs days_of_cover < 14
    row = plan_sku(_sku(current_stock=50), review_period_days=14)
    assert row["status"] == "urgent"


def test_reorder_now_when_cover_between_lead_time_and_reorder_point():
    # reorder_point = 14 + 7 = 21; want days_of_cover in (14, 21) -> stock in (140, 210)
    row = plan_sku(_sku(current_stock=180), review_period_days=14)
    assert row["status"] == "reorder_now"


def test_on_order_missing_is_flagged_and_treated_as_zero():
    sku = _sku(current_stock=50)
    del sku["on_order_qty"]
    row = plan_sku(sku, review_period_days=14)
    assert row["on_order_qty"] == 0
    assert any("on_order_unconfirmed" in f for f in row["flags"])


def test_on_order_reduces_suggested_quantity():
    without = plan_sku(_sku(current_stock=50, on_order_qty=0), review_period_days=14)
    with_stock_in_transit = plan_sku(_sku(current_stock=50, on_order_qty=100), review_period_days=14)
    assert with_stock_in_transit["suggested_order_qty"] < without["suggested_order_qty"]


def test_moq_rounds_up_and_discloses_it():
    row = plan_sku(_sku(current_stock=50, moq=1000), review_period_days=14)
    assert row["suggested_order_qty"] == 1000
    assert row["rounded_to_moq"] is True


def test_unit_cost_produces_labeled_estimate():
    row = plan_sku(_sku(current_stock=50, unit_cost=2.5), review_period_days=14)
    assert row["estimated_order_value"] == round(row["suggested_order_qty"] * 2.5, 2)
    assert row["estimated_order_value_is_estimate"] is True


def test_plan_output_status_is_always_draft():
    report = plan(copy.deepcopy(DEMO_INPUT))
    assert report["status"] == "draft"


def test_plan_summary_counts_match_rows():
    report = plan(copy.deepcopy(DEMO_INPUT))
    counted = sum(report["summary"].values())
    assert counted == len(report["skus"])


def test_empty_sku_list_does_not_crash():
    report = plan({"skus": []})
    assert report["skus"] == []
