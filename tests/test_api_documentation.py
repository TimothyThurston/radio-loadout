"""Production docs are disabled without mutating independent development apps."""

import pytest
from fastapi.testclient import TestClient

from radio_loadout.web.app import app
from radio_loadout.web.app import create_app as create_web_app
from radio_loadout.web.production import SECURITY_HEADERS, create_app

DOC_PATHS = ("/docs", "/redoc", "/docs/oauth2-redirect")
DOC_ASSET_HOSTS = (
    "cdn.jsdelivr.net", "fonts.googleapis.com", "fonts.gstatic.com", "fastapi.tiangolo.com",
)


@pytest.fixture
def production(monkeypatch):
    monkeypatch.setenv("RADIO_LOADOUT_ALLOWED_HOSTS", "testserver")
    return TestClient(create_app())


@pytest.mark.parametrize("path", (*DOC_PATHS, "/docs/", "/redoc/"))
def test_production_docs_return_404_with_security_headers(production, path) -> None:
    response = production.get(path)
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert response.headers["cache-control"] == "no-store"
    for name, value in SECURITY_HEADERS.items():
        assert response.headers[name] == value


@pytest.mark.parametrize("path", DOC_PATHS)
def test_development_docs_remain_available(path) -> None:
    # Both the existing development entry point and fresh instances retain docs.
    for development in (app, create_web_app()):
        response = TestClient(development).get(path)
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "<script" in response.text


def test_raw_openapi_preserves_application_contract_in_both_modes(production) -> None:
    response = production.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == TestClient(app).get("/openapi.json").json()
    assert {"/builder", "/downloads/chirp.csv", "/imports/chirp.csv", "/validation/chirp.csv"} <= (
        response.json()["paths"].keys()
    )
    assert not any(host in response.text for host in DOC_ASSET_HOSTS)


@pytest.mark.parametrize("path", ("/", "/builder"))
def test_production_pages_have_no_dead_docs_links_or_documentation_assets(production, path) -> None:
    response = production.get(path)
    assert response.status_code == 200
    assert "View API" not in response.text
    for reference in (*DOC_PATHS, *DOC_ASSET_HOSTS):
        assert reference not in response.text
    if path == "/":
        development_home = TestClient(app).get("/").text
        assert 'href="/docs"' in development_home
        assert "View API" in development_home


@pytest.mark.parametrize("path", (*DOC_PATHS, "/openapi.json"))
def test_documentation_policy_still_enforces_trusted_hosts(production, path) -> None:
    response = production.get(path, headers={"Host": "untrusted.invalid"})
    assert response.status_code == 400
    assert response.headers["x-content-type-options"] == "nosniff"


def test_application_instances_remain_independent_in_both_creation_orders(monkeypatch) -> None:
    monkeypatch.setenv("RADIO_LOADOUT_ALLOWED_HOSTS", "testserver")
    development = create_web_app()
    original_routes = tuple(app.routes)
    before = TestClient(create_app())
    later_development = create_web_app()
    after = TestClient(create_app())

    @development.get("/development-only")
    def development_only():
        return {"development": True}

    assert TestClient(development).get("/development-only").status_code == 200
    assert TestClient(later_development).get("/development-only").status_code == 404
    for client in (before, after):
        assert client.get("/development-only").status_code == 404
        for path in DOC_PATHS:
            assert client.get(path).status_code == 404
    for instance in (app, development, later_development):
        for path in DOC_PATHS:
            assert TestClient(instance).get(path).status_code == 200
    assert tuple(app.routes) == original_routes
