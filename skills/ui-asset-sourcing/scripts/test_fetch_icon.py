"""fetch_icon 测试: URL 解析 + SVG 校验逻辑 + 网络层替身注入。全部离线——
不依赖真实网络请求，保证 CI 确定性；真实端点的验证见开发时的手动
curl/--library 调用记录（见 exports_gate 同款离线测试哲学）。"""

import urllib.error

import pytest

from fetch_icon import demo, fetch_icon, resolve_url, validate_svg


def test_demo_accepts_valid_rejects_invalid():
    assert demo() == 0


# ───────────────────────────── resolve_url ─────────────────────────────────

def test_resolve_url_known_library():
    url = resolve_url("lucide", "arrow-right")
    assert url == "https://unpkg.com/lucide-static@1.66.0/icons/arrow-right.svg"


def test_resolve_url_normalizes_name():
    # underscores/spaces/case are normalized; splitting camelCase into
    # kebab-case is NOT attempted — registry names are always already
    # kebab-case, so "ArrowRight" as a whole-word input isn't a realistic case
    assert resolve_url("lucide", "arrow_right") == resolve_url("lucide", "arrow-right")
    assert resolve_url("lucide", "  Arrow Right  ") == resolve_url("lucide", "arrow-right")
    assert resolve_url("lucide", "ARROW-RIGHT") == resolve_url("lucide", "arrow-right")


def test_resolve_url_unknown_library_raises():
    with pytest.raises(ValueError, match="unknown library"):
        resolve_url("not-a-real-library", "arrow-right")


def test_resolve_url_error_message_lists_available_libraries():
    with pytest.raises(ValueError, match="lucide"):
        resolve_url("bogus", "x")


# ───────────────────────────── simple-icons slug (not kebab-case) ──────────

@pytest.mark.parametrize("brand,expected_slug", [
    ("American Express", "americanexpress"),
    ("Node.js", "nodedotjs"),
    ("C++", "cplusplus"),
    (".NET", "dotnet"),
    ("Coca-Cola", "cocacola"),
    ("GitHub", "github"),
])
def test_simple_icons_uses_real_slug_convention_not_kebab_case(brand, expected_slug):
    # Simple Icons concatenates words and spells out punctuation instead of
    # hyphenating like the other four registries — confirmed live against
    # unpkg for americanexpress/nodedotjs/cplusplus/dotnet/cocacola before
    # this test was written (a prior version of this function 404'd on all
    # of these by hyphenating "american-express" instead).
    url = resolve_url("simple-icons", brand)
    assert url == f"https://unpkg.com/simple-icons@16.36.0/icons/{expected_slug}.svg"


def test_other_registries_still_use_kebab_case():
    assert "arrow-right" in resolve_url("lucide", "Arrow Right")
    assert "arrow-right" in resolve_url("heroicons", "arrow_right")


# ───────────────────────────── validate_svg ────────────────────────────────

def test_validate_svg_accepts_real_svg():
    ok, reason = validate_svg('<svg viewBox="0 0 24 24"><path d="M5 12h14"/></svg>')
    assert ok is True


def test_validate_svg_rejects_empty():
    ok, reason = validate_svg("")
    assert ok is False
    assert "empty" in reason


def test_validate_svg_rejects_html_error_page():
    ok, reason = validate_svg("<html><body>Cannot GET /icons/nope.svg</body></html>")
    assert ok is False


def test_validate_svg_rejects_svg_tag_with_no_shape():
    # a bare <svg></svg> with no path/circle/rect etc. isn't a usable icon
    ok, reason = validate_svg('<svg viewBox="0 0 24 24"></svg>')
    assert ok is False
    assert "shape" in reason


def test_validate_svg_accepts_circle_and_rect_variants():
    assert validate_svg('<svg><circle cx="12" cy="12" r="10"/></svg>')[0] is True
    assert validate_svg('<svg><rect x="0" y="0" width="10" height="10"/></svg>')[0] is True


# ───────────────────────────── fetch_icon (fetch_fn injected) ──────────────

def test_fetch_icon_success_returns_content_and_hash():
    result = fetch_icon(
        "lucide", "arrow-right",
        fetch_fn=lambda url: '<svg><path d="M5 12h14"/></svg>',
    )
    assert result["ok"] is True
    assert result["content"] == '<svg><path d="M5 12h14"/></svg>'
    assert len(result["sha256"]) == 16


def test_fetch_icon_invalid_response_returns_ok_false_not_raise():
    result = fetch_icon("lucide", "nope", fetch_fn=lambda url: "<html>404</html>")
    assert result["ok"] is False
    assert result["content"] is None


def test_fetch_icon_network_error_returns_ok_false_not_raise():
    def _raise(url):
        raise urllib.error.URLError("connection refused")

    result = fetch_icon("lucide", "arrow-right", fetch_fn=_raise)
    assert result["ok"] is False
    assert "fetch failed" in result["reason"]


def test_fetch_icon_unknown_library_still_raises():
    # resolve_url's ValueError is a usage error, not a runtime outcome —
    # fetch_icon should not swallow it into ok=False
    with pytest.raises(ValueError):
        fetch_icon("bogus-library", "x", fetch_fn=lambda url: "")


def test_fetch_icon_same_content_same_hash():
    fn = lambda url: '<svg><path d="M5 12h14"/></svg>'
    r1 = fetch_icon("lucide", "arrow-right", fetch_fn=fn)
    r2 = fetch_icon("heroicons", "arrow-right", fetch_fn=fn)
    assert r1["sha256"] == r2["sha256"]  # same bytes -> same hash regardless of source


# ───────────────────────────── pinned sources ──────────────────────────────

@pytest.mark.parametrize("library", ["lucide", "heroicons", "tabler", "phosphor", "simple-icons"])
def test_every_registry_is_pinned_to_a_release(library):
    url = resolve_url(library, "arrow-right")
    assert "@latest" not in url and "/master/" not in url and "/main/" not in url


# ───────────────────────────── active content ──────────────────────────────

_SHAPE = '<path d="M5 12h14"/>'


@pytest.mark.parametrize("svg, reason", [
    (f'<svg><script>alert(1)</script>{_SHAPE}</svg>', "<script>"),
    (f'<svg onload="alert(1)">{_SHAPE}</svg>', "on* event"),
    (f'<svg>{_SHAPE[:-2]} onclick="x()"/></svg>', "on* event"),
    (f'<svg><foreignObject><div/></foreignObject>{_SHAPE}</svg>', "foreignObject"),
    (f'<svg><a href="javascript:alert(1)">{_SHAPE}</a></svg>', "javascript:"),
    (f'<svg><a xlink:href=" JavaScript:alert(1)">{_SHAPE}</a></svg>', "javascript:"),
    (f'<svg><use href="https://evil.example/sprite.svg#i"/>{_SHAPE}</svg>', "outside the document"),
    (f'<svg><use xlink:href="sprite.svg#i"/>{_SHAPE}</svg>', "outside the document"),
    (f'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>{_SHAPE}</svg>', "DOCTYPE"),
])
def test_validate_svg_rejects_active_content(svg, reason):
    ok, why = validate_svg(svg)
    assert not ok and reason in why


def test_validate_svg_allows_local_use_reference():
    svg = (f'<svg><defs><g id="i">{_SHAPE}</g></defs>'
           '<use href="#i"/><use xlink:href="#i"/></svg>')
    assert validate_svg(svg) == (True, "ok")


def test_fetch_icon_refuses_unsafe_svg():
    result = fetch_icon("lucide", "x", fetch_fn=lambda url: f'<svg onload="x()">{_SHAPE}</svg>')
    assert result["ok"] is False and result["content"] is None
