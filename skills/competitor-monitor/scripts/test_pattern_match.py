"""pattern_match 测试:demo 分离 + 每个 pattern 单独验证 + 拒绝路径。"""

from pattern_match import DEFAULT_POLICY, DEMO_INPUT, compute_deltas, demo, evaluate, evaluate_competitor


def _competitor(**overrides):
    base = {
        "name": "C",
        "price": {"current": 1000, "prior": 1000},
        "inventory_proxy": {"current": 100, "prior": 100},
        "rank": {"current": 30, "prior": 30},
        "reviews_gained": {"current": 10, "prior": 10},
    }
    base.update(overrides)
    return base


def test_demo_worked_example_and_edge_cases():
    assert demo() == 0


def test_single_signal_refuses_a_verdict():
    row = evaluate_competitor({"name": "C", "price": {"current": 950, "prior": 1000}}, DEFAULT_POLICY)
    assert row["pattern"] == "no_clear_pattern"
    assert row["patterns"] == []


def test_no_signals_at_all_refuses_a_verdict():
    row = evaluate_competitor({"name": "C"}, DEFAULT_POLICY)
    assert row["pattern"] == "no_clear_pattern"


def test_clearance_push_matches_the_worked_example():
    row = evaluate_competitor(DEMO_INPUT["competitors"][0], DEFAULT_POLICY)
    patterns = {m["pattern"] for m in row["patterns"]}
    assert "clearance_push" in patterns


def test_flat_price_with_no_inventory_drop_does_not_trigger_clearance():
    c = _competitor(price={"current": 1000, "prior": 1000},
                     inventory_proxy={"current": 100, "prior": 100},
                     rank={"current": 10, "prior": 40})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "clearance_push" not in {m["pattern"] for m in row["patterns"]}


def test_aggressive_ad_push_needs_flat_price():
    c = _competitor(price={"current": 1000, "prior": 1000},
                     rank={"current": 10, "prior": 40},
                     reviews_gained={"current": 30, "prior": 10})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "aggressive_ad_push" in {m["pattern"] for m in row["patterns"]}


def test_aggressive_ad_push_excluded_when_price_actually_drops():
    c = _competitor(price={"current": 890, "prior": 1000},
                     rank={"current": 10, "prior": 40},
                     reviews_gained={"current": 30, "prior": 10})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "aggressive_ad_push" not in {m["pattern"] for m in row["patterns"]}


def test_stockout_risk_matches_inventory_down_price_steady_rank_down():
    c = _competitor(price={"current": 1005, "prior": 1000},
                     inventory_proxy={"current": 20, "prior": 90},
                     rank={"current": 61, "prior": 40})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert row["pattern"] == "stockout_risk"


def test_price_war_signal_without_inventory_drop():
    c = _competitor(price={"current": 900, "prior": 1000},
                     inventory_proxy={"current": 100, "prior": 100})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "price_war_signal" in {m["pattern"] for m in row["patterns"]}


def test_fading_listing_matches_declining_rank_and_review_velocity():
    c = _competitor(rank={"current": 80, "prior": 40},
                     reviews_gained={"current": 3, "prior": 12},
                     inventory_proxy={"current": 100, "prior": 100})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "fading_listing" in {m["pattern"] for m in row["patterns"]}


def test_restock_recovery_matches_inventory_up_price_flat():
    c = _competitor(inventory_proxy={"current": 150, "prior": 90},
                     price={"current": 1000, "prior": 1000})
    row = evaluate_competitor(c, DEFAULT_POLICY)
    assert "restock_recovery" in {m["pattern"] for m in row["patterns"]}


def test_zero_prior_reviews_flagged_not_computed_as_ratio():
    deltas = compute_deltas({"reviews_gained": {"current": 15, "prior": 0}})
    assert deltas.get("new_review_activity") is True
    assert "review_velocity_ratio" not in deltas


def test_rank_change_sign_convention_improvement_is_positive():
    deltas = compute_deltas({"rank": {"current": 10, "prior": 40}})
    assert deltas["rank_change"] == 30


def test_portfolio_ranks_most_corroborated_competitor_first():
    report = evaluate(DEMO_INPUT)
    # Competitor X (2 usable signals -> 1 pattern) and Y (1 pattern) both rank
    # above Z (no_clear_pattern, single signal).
    names_in_order = [c["competitor"] for c in report["competitors"]]
    assert names_in_order.index("Competitor Z") == len(names_in_order) - 1


def test_empty_competitor_list_does_not_crash():
    report = evaluate({"competitors": []})
    assert report["competitors"] == []
