from app import create_app


def test_browser_home_serves_dashboard_and_assets():
    client = create_app(seed=[]).test_client()
    response = client.get('/', headers={'Accept': 'text/html'})
    assert response.status_code == 200
    assert response.mimetype == 'text/html'
    assert b'id="inventory-body"' in response.data
    for path in ['/static/styles.css', '/static/app.js']:
        assert client.get(path).status_code == 200


def test_api_metadata_stays_json_even_with_browser_accept_header(monkeypatch):
    monkeypatch.setenv('APP_VERSION', 'ui-release')
    response = create_app(seed=[]).test_client().get('/api', headers={'Accept': 'text/html'})
    assert response.mimetype == 'application/json'
    assert response.json['version'] == 'ui-release'
