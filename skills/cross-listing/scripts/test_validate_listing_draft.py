"""validate_listing_draft 测试:demo 分离 + 各门禁逐一验证。"""

import copy

from validate_listing_draft import GOOD_DRAFT, demo, validate


def _good():
    return copy.deepcopy(GOOD_DRAFT)


def test_demo_gate_separates_draft_from_premature_publish():
    assert demo() == 0


def test_good_draft_passes_clean():
    rep = validate(_good())
    assert rep["verdict"] == "PASS" and rep["flags"] == []
    assert rep["next_step"] == "hand_to_seller_for_review"


def test_missing_required_field_fails():
    d = _good()
    del d["title"]
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "missing_field" in {f["code"] for f in rep["flags"]}


def test_published_status_fails_mechanically():
    d = _good()
    d["status"] = "published"
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "publish_not_allowed" in {f["code"] for f in rep["flags"]}


def test_live_status_also_fails():
    d = _good()
    d["status"] = "live"
    assert "publish_not_allowed" in {f["code"] for f in validate(d)["flags"]}


def test_unmapped_category_fails():
    d = _good()
    d["category"]["destination_id"] = None
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "unmapped_category" in {f["code"] for f in rep["flags"]}


def test_lost_linkage_fails():
    d = _good()
    d["source_sku"] = "   "
    assert "linkage_lost" in {f["code"] for f in validate(d)["flags"]}


def test_undisclosed_image_drop_fails():
    d = _good()
    d["images"] = d["images"][:1]
    d["source_image_count"] = 2
    d["images_omitted_reason"] = None
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "undisclosed_image_drop" in {f["code"] for f in rep["flags"]}


def test_disclosed_image_drop_does_not_fail_on_that_code():
    d = _good()
    d["images"] = d["images"][:1]
    d["source_image_count"] = 2
    d["images_omitted_reason"] = "second image was a duplicate angle, dropped intentionally"
    codes = {f["code"] for f in validate(d)["flags"]}
    assert "undisclosed_image_drop" not in codes


def test_fabricated_dimensions_flagged_when_unknown_but_populated():
    d = _good()
    d["dimensions_source"] = "unknown"
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "fabricated_dimensions" in {f["code"] for f in rep["flags"]}


def test_invalid_dimensions_source_value_fails():
    d = _good()
    d["dimensions_source"] = "estimated"
    assert "fabricated_dimensions" in {f["code"] for f in validate(d)["flags"]}


def test_large_price_delta_without_confirmation_fails():
    d = _good()
    d["price"]["destination_amount"] = d["price"]["source_amount"] * 2
    d["price"]["delta_pct"] = 1.0
    d["price"]["price_change_confirmed"] = False
    rep = validate(d)
    assert rep["verdict"] == "FAIL"
    assert "price_change_unconfirmed" in {f["code"] for f in rep["flags"]}


def test_large_price_delta_with_confirmation_passes_that_check():
    d = _good()
    d["price"]["destination_amount"] = d["price"]["source_amount"] * 2
    d["price"]["delta_pct"] = 1.0
    d["price"]["price_change_confirmed"] = True
    codes = {f["code"] for f in validate(d)["flags"]}
    assert "price_change_unconfirmed" not in codes


def test_small_price_delta_needs_no_confirmation():
    d = _good()
    d["price"]["destination_amount"] = d["price"]["source_amount"] * 1.05
    d["price"]["delta_pct"] = 0.05
    codes = {f["code"] for f in validate(d)["flags"]}
    assert "price_change_unconfirmed" not in codes


def test_unconfirmed_certifications_warns_not_fails():
    d = _good()
    d["certifications_verbatim"] = False
    rep = validate(d)
    assert rep["verdict"] != "FAIL"
    assert "certifications_unconfirmed" in {f["code"] for f in rep["flags"]}
