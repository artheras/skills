"""ads_bid_optimizer 测试:demo 分离 + 每条规则单独验证 + 优先级顺序验证。"""

import pytest

from ads_bid_optimizer import DEMO_INPUT, _resolve_policy, demo, evaluate, evaluate_campaign


def _policy(**overrides):
    p = {"target_acos": 0.35}
    p.update(overrides)
    return _resolve_policy(p)


def test_demo_fires_all_five_branches():
    assert demo() == 0


def test_missing_target_acos_raises():
    with pytest.raises(ValueError):
        _resolve_policy({})


def test_low_spend_is_insufficient_data_regardless_of_acos():
    campaign = {"name": "X", "spend": 100, "ad_attributed_revenue": 1000, "orders": 5}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "insufficient_data"


def test_zero_orders_recommends_pause_not_decrease():
    campaign = {"name": "X", "spend": 6000, "ad_attributed_revenue": 0, "orders": 0}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "recommend_pause"


def test_zero_orders_beats_high_acos_priority():
    # Even with revenue present but zero orders somehow (edge case), pause still
    # takes priority over the ACOS-based rules — order matters.
    campaign = {"name": "X", "spend": 6000, "ad_attributed_revenue": 5000, "orders": 0}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "recommend_pause"


def test_high_acos_low_orders_recommends_decrease():
    campaign = {"name": "X", "spend": 7830, "ad_attributed_revenue": 16312.5, "orders": 1}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "recommend_decrease_bid"
    assert row["adjustment_pct"] == -0.15


def test_high_acos_but_enough_orders_does_not_trigger_decrease():
    campaign = {"name": "X", "spend": 7830, "ad_attributed_revenue": 16312.5, "orders": 10}
    row = evaluate_campaign(campaign, _policy(min_orders_low_threshold=2))
    assert row["action"] != "recommend_decrease_bid"


def test_decrease_step_capped_at_max_step_pct():
    campaign = {"name": "X", "spend": 7830, "ad_attributed_revenue": 16312.5, "orders": 1}
    row = evaluate_campaign(campaign, _policy(decrease_step_pct=0.9, max_step_pct=0.25))
    assert row["adjustment_pct"] == -0.25


def test_efficient_and_budget_constrained_recommends_increase():
    campaign = {"name": "X", "spend": 5400, "ad_attributed_revenue": 27000, "orders": 45,
                "daily_budget": 5500}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "recommend_increase_bid"


def test_efficient_but_not_budget_constrained_does_not_recommend_increase():
    campaign = {"name": "X", "spend": 5400, "ad_attributed_revenue": 27000, "orders": 45,
                "daily_budget": 50000}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "no_action"


def test_efficient_without_daily_budget_does_not_crash_or_recommend_increase():
    campaign = {"name": "X", "spend": 5400, "ad_attributed_revenue": 27000, "orders": 45}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "no_action"


def test_increase_step_capped_at_max_step_pct():
    campaign = {"name": "X", "spend": 5400, "ad_attributed_revenue": 27000, "orders": 45,
                "daily_budget": 5500}
    row = evaluate_campaign(campaign, _policy(increase_step_pct=0.9, max_step_pct=0.25))
    assert row["adjustment_pct"] == 0.25


def test_healthy_campaign_inside_band_is_no_action():
    campaign = {"name": "X", "spend": 9000, "ad_attributed_revenue": 30000, "orders": 25,
                "daily_budget": 20000}
    row = evaluate_campaign(campaign, _policy())
    assert row["action"] == "no_action"


def test_evaluate_returns_one_row_per_campaign():
    report = evaluate(DEMO_INPUT)
    assert len(report["recommendations"]) == len(DEMO_INPUT["campaigns"])


def test_no_recommendation_ever_contains_a_mutating_action():
    report = evaluate(DEMO_INPUT)
    allowed_actions = {"insufficient_data", "recommend_pause", "recommend_decrease_bid",
                        "recommend_increase_bid", "no_action"}
    for row in report["recommendations"]:
        assert row["action"] in allowed_actions


def test_empty_campaign_list_does_not_crash():
    report = evaluate({"policy": {"target_acos": 0.35}, "campaigns": []})
    assert report["recommendations"] == []
