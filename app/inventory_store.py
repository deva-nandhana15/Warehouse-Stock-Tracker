"""Inventory backends; Azure updates use ETags to prevent lost stock changes."""
import os
import threading
from urllib.parse import urlparse

from azure.core import MatchConditions
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError, ResourceModifiedError
from azure.data.tables import TableClient, UpdateMode, EntityProperty, EdmType
from azure.identity import AzureCliCredential, ManagedIdentityCredential

MAX_QUANTITY = 9_007_199_254_740_991


class InventoryError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


def adjusted_quantity(current, quantity, direction):
    if direction == 'issue' and quantity > current:
        raise InventoryError('insufficient stock', 409)
    result = current + (quantity if direction == 'receive' else -quantity)
    if result > MAX_QUANTITY:
        raise InventoryError('quantity exceeds supported maximum', 409)
    return result


class MemoryInventory:
    backend = 'memory'
    persistent = False

    def __init__(self, seed):
        self.items = {item['sku']: dict(item) for item in seed}
        self.lock = threading.Lock()

    def list_items(self):
        with self.lock:
            return sorted((dict(item) for item in self.items.values()), key=lambda item: item['sku'])

    def add(self, item):
        with self.lock:
            if item['sku'] in self.items:
                raise InventoryError('sku already exists', 409)
            self.items[item['sku']] = dict(item)
            return dict(item)

    def adjust(self, sku, quantity, direction):
        with self.lock:
            if sku not in self.items:
                raise InventoryError('sku not found', 404)
            item = self.items[sku]
            item['quantity'] = adjusted_quantity(item['quantity'], quantity, direction)
            return dict(item)

    def check_ready(self):
        return None


class AzureTableInventory:
    backend = 'azure-table'
    persistent = True
    partition = 'inventory'

    def __init__(self, client):
        self.client = client

    @classmethod
    def from_environment(cls):
        endpoint = os.environ.get('AZURE_TABLE_ENDPOINT', '')
        parsed = urlparse(endpoint)
        # No account keys/SAS URLs; only the HTTPS Azure Tables endpoint.
        if (parsed.scheme != 'https' or not parsed.hostname
                or not parsed.hostname.endswith('.table.core.windows.net')
                or parsed.query or parsed.fragment or parsed.username or parsed.password
                or parsed.path not in ('', '/') or parsed.port not in (None, 443)):
            raise ValueError('AZURE_TABLE_ENDPOINT must be an HTTPS Azure Table Storage endpoint without credentials')
        auth = os.environ.get('AZURE_AUTH_MODE', 'managed-identity')
        if auth == 'managed-identity':
            client_id = os.environ.get('AZURE_CLIENT_ID')
            credential = ManagedIdentityCredential(client_id=client_id) if client_id else ManagedIdentityCredential()
        elif auth == 'azure-cli':
            credential = AzureCliCredential()
        else:
            raise ValueError('AZURE_AUTH_MODE must be managed-identity or azure-cli')
        return cls(TableClient(endpoint, os.environ.get('AZURE_TABLE_NAME', 'inventory'),
                               credential=credential, retry_total=2, connection_timeout=5, read_timeout=10))

    @staticmethod
    def _item(entity):
        def number(value):
            return int(value.value if isinstance(value, EntityProperty) else value)
        return {'sku': entity['RowKey'], 'name': entity['name'],
                'quantity': number(entity['quantity']), 'reorder_level': number(entity['reorder_level'])}

    def _entity(self, item):
        return {'PartitionKey': self.partition, 'RowKey': item['sku'], 'name': item['name'],
                'quantity': EntityProperty(item['quantity'], EdmType.INT64),
                'reorder_level': EntityProperty(item['reorder_level'], EdmType.INT64)}

    def list_items(self):
        entities = self.client.query_entities("PartitionKey eq 'inventory'")
        return sorted((self._item(entity) for entity in entities), key=lambda item: item['sku'])

    def add(self, item):
        try:
            self.client.create_entity(self._entity(item))
        except ResourceExistsError as exc:
            raise InventoryError('sku already exists', 409) from exc
        return dict(item)

    def adjust(self, sku, quantity, direction):
        # The SDK must not replay an ambiguous stock update after a transport error.
        # ETags also protect each retry from overwriting another client's update.
        for _ in range(5):
            try:
                entity = self.client.get_entity(self.partition, sku)
            except ResourceNotFoundError as exc:
                raise InventoryError('sku not found', 404) from exc
            item = self._item(entity)
            item['quantity'] = adjusted_quantity(item['quantity'], quantity, direction)
            try:
                self.client.update_entity(self._entity(item), mode=UpdateMode.REPLACE,
                                          etag=entity.metadata['etag'],
                                          match_condition=MatchConditions.IfNotModified,
                                          retry_total=0)
                return item
            except ResourceModifiedError:
                continue
            except ResourceNotFoundError as exc:
                raise InventoryError('sku not found', 404) from exc
        raise InventoryError('stock changed concurrently; refresh and try again', 409)

    def check_ready(self):
        next(iter(self.client.query_entities("PartitionKey eq 'inventory'", select=['RowKey'],
                                             results_per_page=1)), None)
