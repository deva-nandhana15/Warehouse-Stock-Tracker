"""Integration test against a disposable, loopback-only official Azurite container.

Uses a deterministic public test credential solely inside the local emulator.
Never connects to Azure or uses the developer's Azure identity.
"""
import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
import time

from azure.core.credentials import AzureNamedKeyCredential
from azure.data.tables import TableClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from app import create_app
from inventory_store import AzureTableInventory, InventoryError

image = 'mcr.microsoft.com/azure-storage/azurite:3.37.0'
account = 'localwarehouse'
# Deliberately public emulator-only credential, not an Azure account key.
test_key = base64.b64encode(b'public-local-emulator-fixture-only').decode()
container = None


def command(*args):
    return subprocess.check_output(args, text=True).strip()


try:
    container = command('docker', 'run', '-d', '--rm', '-p', '127.0.0.1::10002',
                        '-e', f'AZURITE_ACCOUNTS={account}:{test_key}', image,
                        'azurite-table', '--tableHost', '0.0.0.0', '--skipApiVersionCheck', '--silent')
    port = command('docker', 'port', container, '10002/tcp').rsplit(':', 1)[1]
    endpoint = f'http://127.0.0.1:{port}/{account}'

    def client():
        return TableClient(endpoint, 'inventory', credential=AzureNamedKeyCredential(account, test_key),
                           retry_total=0, connection_timeout=2)

    table = client()
    for attempt in range(30):
        try:
            table.create_table()
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(0.2)
    first = create_app(store=AzureTableInventory(table)).test_client()
    assert first.post('/items', json={'sku': 'PERSIST-1', 'name': 'Persistence fixture',
                                    'quantity': 10, 'reorder_level': 5}).status_code == 201
    assert first.post('/items/PERSIST-1/receive', json={'quantity': 5}).json['quantity'] == 15
    # A new Flask app and new SDK client must read the same records.
    second = create_app(store=AzureTableInventory(client())).test_client()
    assert second.get('/items').json[0]['quantity'] == 15
    assert second.post('/items/PERSIST-1/issue', json={'quantity': 11}).json['quantity'] == 4
    assert first.get('/alerts/low-stock').json[0]['sku'] == 'PERSIST-1'
    assert second.post('/items/PERSIST-1/issue', json={'quantity': 5}).status_code == 409

    def issue_one(_):
        store = AzureTableInventory(client())
        try:
            store.adjust('PERSIST-1', 1, 'issue')
            return True
        except InventoryError as error:
            assert error.status == 409
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(issue_one, range(8)))
    assert sum(results) == 4
    assert second.get('/items').json[0]['quantity'] == 0
    assert second.get('/ready').status_code == 200
    print('PASS: persistence across app instances, stock changes, insufficient stock, concurrent issues, readiness')
finally:
    if container:
        subprocess.run(['docker', 'stop', container], check=True, stdout=subprocess.DEVNULL)
