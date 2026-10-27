"""Generate the checked-in Postman collection without external packages."""
import json
from pathlib import Path

cases = [
    ('Health', 'GET', '/health', None, 200, 'pm.expect(pm.response.json().status).to.eql("ok");'),
    ('Version', 'GET', '/', None, 200, 'pm.expect(pm.response.json().name).to.eql("Warehouse Stock Tracker");'),
    ('List items', 'GET', '/items', None, 200, 'pm.expect(pm.response.json()).to.be.an("array");'),
    ('Add item', 'POST', '/items', {'sku': '{{sku}}', 'name': 'API test item', 'quantity': 10, 'reorder_level': 5}, 201, 'pm.expect(pm.response.json().quantity).to.eql(10);'),
    ('Duplicate item', 'POST', '/items', {'sku': '{{sku}}', 'name': 'Duplicate'}, 409, ''),
    ('Receive', 'POST', '/items/{{sku}}/receive', {'quantity': 5}, 200, 'pm.expect(pm.response.json().quantity).to.eql(15);'),
    ('Issue', 'POST', '/items/{{sku}}/issue', {'quantity': 11}, 200, 'pm.expect(pm.response.json().quantity).to.eql(4);'),
    ('Insufficient stock', 'POST', '/items/{{sku}}/issue', {'quantity': 5}, 409, 'pm.expect(pm.response.json().error).to.eql("insufficient stock");'),
    ('Stock unchanged', 'GET', '/items', None, 200, 'pm.expect(pm.response.json().find(i => i.sku === pm.collectionVariables.get("sku")).quantity).to.eql(4);'),
    ('Low stock', 'GET', '/alerts/low-stock', None, 200, 'pm.expect(pm.response.json().some(i => i.sku === pm.collectionVariables.get("sku"))).to.eql(true);'),
    ('Invalid quantity', 'POST', '/items/{{sku}}/receive', {'quantity': True}, 400, ''),
    ('Unknown SKU', 'POST', '/items/MISSING-{{$guid}}/receive', {'quantity': 1}, 404, ''),
]
items = []
for name, method, path, body, status, assertion in cases:
    if not assertion:
        assertion = 'pm.expect(pm.response.json().error).to.be.a("string");'
    request = {'method': method, 'header': [], 'url': '{{baseUrl}}' + path}
    if body is not None:
        request['header'] = [{'key': 'Content-Type', 'value': 'application/json'}]
        request['body'] = {'mode': 'raw', 'raw': json.dumps(body)}
    events = [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': [
        f'pm.test("{name}: status", () => pm.response.to.have.status({status}));',
        'pm.test("Security headers", () => pm.expect(pm.response.headers.get("X-Content-Type-Options")).to.eql("nosniff"));',
        'pm.test("Response content", () => { ' + assertion + ' });',
    ]}}]
    if name == 'Health':
        events.insert(0, {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': [
            'pm.collectionVariables.set("sku", "API-" + pm.variables.replaceIn("{{$guid}}").replace(/-/g, "").slice(0, 24));'
        ]}})
    items.append({'name': name, 'request': request, 'event': events})
collection = {
    'info': {'name': 'Warehouse Stock Tracker', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
    'variable': [{'key': 'baseUrl', 'value': 'http://127.0.0.1:5000'}], 'item': items,
}
target = Path(__file__).resolve().parents[1] / 'postman' / 'collection.json'
target.parent.mkdir(exist_ok=True)
target.write_text(json.dumps(collection, indent=2) + '\n', encoding='utf-8')
