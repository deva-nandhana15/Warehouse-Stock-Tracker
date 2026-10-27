"""Warehouse Stock Tracker - a deliberately small inventory REST API.

Uses in-memory storage locally or Azure Table Storage for persistent deployments.
"""
import os
import re

from flask import Flask, jsonify, render_template, request
from azure.core.exceptions import AzureError
from inventory_store import AzureTableInventory, InventoryError, MemoryInventory, MAX_QUANTITY

SKU_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,32}$")

DEFAULT_SEED = [
    {"sku": "WH-001", "name": "Pallet Jack", "quantity": 12, "reorder_level": 5},
    {"sku": "WH-002", "name": "Packing Tape (roll)", "quantity": 4, "reorder_level": 20},
    {"sku": "WH-003", "name": "Cardboard Box (large)", "quantity": 150, "reorder_level": 50},
]


def _is_int(value):
    # bool is a subclass of int in Python; reject it explicitly.
    return isinstance(value, int) and not isinstance(value, bool)


def _error(message, status):
    return jsonify({"error": message}), status


def create_app(seed=None, store=None):
    app = Flask(__name__)
    if store is None:
        # Explicit seed data is for isolated tests; never seed/reset cloud inventory.
        backend = 'memory' if seed is not None else os.environ.get('STORAGE_BACKEND', 'memory')
        if backend == 'azure-table':
            store = AzureTableInventory.from_environment()
        elif backend == 'memory':
            store = MemoryInventory(DEFAULT_SEED if seed is None else seed)
        else:
            raise ValueError('STORAGE_BACKEND must be memory or azure-table')
    app.extensions['inventory_store'] = store

    @app.errorhandler(InventoryError)
    def inventory_error(error):
        return _error(str(error), error.status)

    @app.errorhandler(AzureError)
    def storage_error(error):
        # SDK exception text may contain request details; never expose it to clients.
        app.logger.warning('Azure storage operation failed (%s)', type(error).__name__)
        return _error('inventory storage unavailable; refresh and try again', 503)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/")
    @app.get("/api")
    def index():
        if request.path == "/" and request.accept_mimetypes.best_match(
            ["text/html", "application/json"]
        ) == "text/html":
            return render_template("index.html")
        return jsonify(
            {
                "name": "Warehouse Stock Tracker",
                "version": os.environ.get("APP_VERSION", "dev"),
            }
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.get('/ready')
    def ready():
        store.check_ready()
        return jsonify({'status': 'ready', 'storage': store.backend})

    @app.get('/storage')
    def storage_info():
        return jsonify({'backend': store.backend, 'persistent': store.persistent})

    @app.get("/items")
    def list_items():
        return jsonify(store.list_items()), 200

    @app.post("/items")
    def add_item():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Request body must be a JSON object", 400)

        sku, name = data.get("sku"), data.get("name")
        quantity = data.get("quantity", 0)
        reorder_level = data.get("reorder_level", 0)

        if not isinstance(sku, str) or not SKU_PATTERN.fullmatch(sku):
            return _error("sku must be 1-32 characters: letters, digits, '_' or '-'", 400)
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
            return _error("name must be a string of 1-100 characters", 400)
        if not _is_int(quantity) or not 0 <= quantity <= MAX_QUANTITY:
            return _error("quantity must be an integer >= 0", 400)
        if not _is_int(reorder_level) or not 0 <= reorder_level <= MAX_QUANTITY:
            return _error("reorder_level must be an integer >= 0", 400)

        item = {'sku': sku, 'name': name.strip(), 'quantity': quantity, 'reorder_level': reorder_level}
        return jsonify(store.add(item)), 201

    def _adjust(sku, direction):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Request body must be a JSON object", 400)
        quantity = data.get("quantity")
        if not _is_int(quantity) or not 0 < quantity <= MAX_QUANTITY:
            return _error("quantity must be a positive integer", 400)

        return jsonify(store.adjust(sku, quantity, direction)), 200

    @app.post("/items/<sku>/receive")
    def receive(sku):
        return _adjust(sku, "receive")

    @app.post("/items/<sku>/issue")
    def issue(sku):
        return _adjust(sku, "issue")

    @app.get("/alerts/low-stock")
    def low_stock():
        return jsonify([item for item in store.list_items() if item['quantity'] <= item['reorder_level']]), 200

    return app


if __name__ == "__main__":
    # Local development only. In the container, gunicorn serves the app.
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
