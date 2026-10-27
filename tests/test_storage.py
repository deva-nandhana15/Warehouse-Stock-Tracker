from unittest.mock import Mock

import pytest
from azure.core.exceptions import AzureError, ResourceExistsError, ResourceModifiedError, ResourceNotFoundError
from azure.data.tables import EntityProperty, EdmType

from app import create_app
from inventory_store import AzureTableInventory, InventoryError, MemoryInventory, MAX_QUANTITY

ITEM = {'sku': 'TEST-1', 'name': 'Widget', 'quantity': 10, 'reorder_level': 5}


def test_azure_int64_properties_decode_to_json_numbers():
    entity = dict(RowKey='TEST-1', name='Widget', quantity=EntityProperty(10, EdmType.INT64),
                  reorder_level=EntityProperty(5, EdmType.INT64))
    assert AzureTableInventory._item(entity) == ITEM


class Entity(dict):
    metadata = {'etag': 'version-1'}


def test_memory_reads_are_copies():
    store = MemoryInventory([ITEM])
    store.list_items()[0]['quantity'] = 999
    assert store.list_items()[0]['quantity'] == 10


def test_azure_duplicate_does_not_overwrite():
    client = Mock()
    client.create_entity.side_effect = ResourceExistsError('duplicate')
    with pytest.raises(InventoryError, match='sku already exists') as error:
        AzureTableInventory(client).add(ITEM)
    assert error.value.status == 409
    client.update_entity.assert_not_called()


def test_conflict_rereads_quantity_before_retrying():
    client = Mock()
    first = Entity(PartitionKey='inventory', RowKey='TEST-1', name='Widget', quantity=10, reorder_level=5)
    second = Entity(first, quantity=7)
    second.metadata = {'etag': 'version-2'}
    client.get_entity.side_effect = [first, second]
    client.update_entity.side_effect = [ResourceModifiedError('conflict'), None]
    result = AzureTableInventory(client).adjust('TEST-1', 4, 'issue')
    assert result['quantity'] == 3
    assert client.update_entity.call_args.kwargs['etag'] == 'version-2'
    assert client.update_entity.call_args.kwargs['retry_total'] == 0


def test_concurrent_issue_cannot_overdraw_stock():
    client = Mock()
    first = Entity(PartitionKey='inventory', RowKey='TEST-1', name='Widget', quantity=10, reorder_level=5)
    second = Entity(first, quantity=2)
    client.get_entity.side_effect = [first, second]
    client.update_entity.side_effect = ResourceModifiedError('conflict')
    with pytest.raises(InventoryError, match='insufficient stock'):
        AzureTableInventory(client).adjust('TEST-1', 8, 'issue')
    assert client.update_entity.call_count == 1


def test_conflict_retries_are_bounded():
    client = Mock()
    client.get_entity.return_value = Entity(PartitionKey='inventory', RowKey='TEST-1', name='Widget', quantity=10, reorder_level=5)
    client.update_entity.side_effect = ResourceModifiedError('conflict')
    with pytest.raises(InventoryError, match='stock changed concurrently'):
        AzureTableInventory(client).adjust('TEST-1', 1, 'receive')
    assert client.update_entity.call_count == 5


def test_unknown_azure_item_maps_to_404():
    client = Mock()
    client.get_entity.side_effect = ResourceNotFoundError('missing')
    response = create_app(store=AzureTableInventory(client)).test_client().post('/items/NOPE/issue', json={'quantity': 1})
    assert response.status_code == 404


def test_storage_failure_returns_503_without_sdk_details():
    client = Mock()
    client.query_entities.side_effect = AzureError('internal request details must stay private')
    app = create_app(store=AzureTableInventory(client)).test_client()
    response = app.get('/items')
    assert response.status_code == 503
    assert b'internal request' not in response.data
    assert app.get('/ready').status_code == 503
    assert app.get('/health').status_code == 200


def test_azure_mode_does_not_seed_or_recreate_table():
    client = Mock()
    client.query_entities.return_value = iter([])
    app = create_app(store=AzureTableInventory(client)).test_client()
    assert app.get('/storage').json == {'backend': 'azure-table', 'persistent': True}
    assert app.get('/items').json == []
    client.create_entity.assert_not_called()
    client.create_table.assert_not_called()


@pytest.mark.parametrize('endpoint', ['http://example.table.core.windows.net', 'https://evil.example',
                                     'https://x.table.core.windows.net/?sig=example'])
def test_cloud_endpoint_rejects_http_foreign_hosts_and_sas(monkeypatch, endpoint):
    monkeypatch.setenv('AZURE_TABLE_ENDPOINT', endpoint)
    with pytest.raises(ValueError):
        AzureTableInventory.from_environment()


def test_quantity_cap_applies_to_creation_and_adjustment():
    app = create_app(seed=[]).test_client()
    assert app.post('/items', json=dict(ITEM, quantity=MAX_QUANTITY + 1)).status_code == 400
    assert app.post('/items', json=dict(ITEM, quantity=MAX_QUANTITY)).status_code == 201
    assert app.post('/items/TEST-1/receive', json={'quantity': 1}).status_code == 409


def test_seeded_tests_ignore_cloud_environment(monkeypatch):
    monkeypatch.setenv('STORAGE_BACKEND', 'azure-table')
    assert create_app(seed=[]).test_client().get('/storage').json['backend'] == 'memory'
