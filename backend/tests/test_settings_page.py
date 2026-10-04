from app.main import app, web_page


def test_settings_page_is_registered() -> None:
    assert any(getattr(route, "path", None) == "/settings" for route in app.routes)
    response = web_page("settings.html", "/settings")
    assert b"aria-current=\"page\"" in response.body


def test_knowledge_page_uses_the_same_navigation() -> None:
    body = web_page("knowledge.html", "/knowledge").body.decode()
    assert 'href="/settings">Настройки</a>' in body
    assert 'href="/knowledge" aria-current="page">База знаний</a>' in body
    assert 'href="/docs">API</a>' not in body
    assert "/assets/knowledge-groups.js" in body
    assert 'id="profile-select"' not in body
    assert "/assets/knowledge-profile-bridge.js" in body


def test_inspection_page_uses_the_same_navigation() -> None:
    body = web_page("inspection.html", "/inspect").body.decode()
    assert 'href="/settings">Настройки</a>' in body
    assert 'href="/inspect" aria-current="page">Проверка авто</a>' in body
    assert 'href="/catalog">Каталог</a>' not in body


def test_fleet_page_receives_common_theme_and_navigation() -> None:
    body = web_page("fleet.html", "/fleet").body.decode()
    assert "/assets/blue-theme.css" in body
    assert 'href="/settings">Настройки</a>' in body
