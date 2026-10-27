import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app(
        seed=[
            {"sku": "A-1", "name": "Widget", "quantity": 10, "reorder_level": 5},
            {"sku": "B-2", "name": "Gadget", "quantity": 3, "reorder_level": 5},
        ]
    )
    app.config["TESTING"] = True
    return app.test_client()


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_shows_name_and_version(client, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "abc1234")
    body = client.get("/").get_json()
    assert body == {"name": "Warehouse Stock Tracker", "version": "abc1234"}


def test_index_version_defaults_to_dev(client, monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    assert client.get("/").get_json()["version"] == "dev"


def test_list_items_sorted_by_sku(client):
    skus = [i["sku"] for i in client.get("/items").get_json()]
    assert skus == ["A-1", "B-2"]


def test_add_item_success(client):
    resp = client.post("/items", json={"sku": "C-3", "name": " Bolt ", "quantity": 7})
    assert resp.status_code == 201
    assert resp.get_json() == {"sku": "C-3", "name": "Bolt", "quantity": 7, "reorder_level": 0}


def test_add_duplicate_sku_conflicts(client):
    resp = client.post("/items", json={"sku": "A-1", "name": "Dup"})
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "payload",
    [
        {"sku": "bad sku!", "name": "X"},
        {"sku": "OK\n", "name": "X"},
        {"sku": "", "name": "X"},
        {"sku": "X" * 33, "name": "X"},
        {"sku": "OK", "name": ""},
        {"sku": "OK", "name": "X", "quantity": -1},
        {"sku": "OK", "name": "X", "quantity": "5"},
        {"sku": "OK", "name": "X", "quantity": True},
        {"sku": "OK", "name": "X", "reorder_level": -2},
    ],
)
def test_add_item_validation(client, payload):
    assert client.post("/items", json=payload).status_code == 400


def test_add_item_rejects_non_object_body(client):
    resp = client.post("/items", data="not json", content_type="application/json")
    assert resp.status_code == 400


def test_receive_increases_stock(client):
    resp = client.post("/items/A-1/receive", json={"quantity": 5})
    assert resp.status_code == 200
    assert resp.get_json()["quantity"] == 15


def test_issue_decreases_stock(client):
    resp = client.post("/items/A-1/issue", json={"quantity": 4})
    assert resp.status_code == 200
    assert resp.get_json()["quantity"] == 6


def test_issue_more_than_stock_is_rejected_and_stock_unchanged(client):
    resp = client.post("/items/B-2/issue", json={"quantity": 4})
    assert resp.status_code == 409
    items = {i["sku"]: i for i in client.get("/items").get_json()}
    assert items["B-2"]["quantity"] == 3


def test_issue_exact_stock_reaches_zero(client):
    resp = client.post("/items/B-2/issue", json={"quantity": 3})
    assert resp.status_code == 200
    assert resp.get_json()["quantity"] == 0


@pytest.mark.parametrize("qty", [0, -5, "3", 1.5, True, None])
@pytest.mark.parametrize("action", ["receive", "issue"])
def test_adjust_rejects_bad_quantity(client, action, qty):
    resp = client.post(f"/items/A-1/{action}", json={"quantity": qty})
    assert resp.status_code == 400


def test_adjust_unknown_sku_returns_404(client):
    assert client.post("/items/NOPE/receive", json={"quantity": 1}).status_code == 404


def test_low_stock_alert_lists_items_at_or_below_reorder_level(client):
    assert [i["sku"] for i in client.get("/alerts/low-stock").get_json()] == ["B-2"]
    client.post("/items/A-1/issue", json={"quantity": 5})  # 10 -> 5 == reorder level
    assert [i["sku"] for i in client.get("/alerts/low-stock").get_json()] == ["A-1", "B-2"]


def test_security_headers_present(client):
    resp = client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Cache-Control"] == "no-store"
