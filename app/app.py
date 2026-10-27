"""Warehouse Stock Tracker - a deliberately small inventory REST API.

Storage is in-memory (resets when the process restarts). This is a documented
limitation of the project, not an oversight: the focus is the DevSecOps pipeline.
"""
import os
import re
import threading

from flask import Flask, jsonify, render_template, request

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


def create_app(seed=None):
    app = Flask(__name__)
    inventory = {}
    lock = threading.Lock()

    for item in DEFAULT_SEED if seed is None else seed:
        inventory[item["sku"]] = dict(item)

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

    @app.get("/items")
    def list_items():
        with lock:
            items = sorted(inventory.values(), key=lambda i: i["sku"])
            return jsonify(items), 200

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
        if not _is_int(quantity) or quantity < 0:
            return _error("quantity must be an integer >= 0", 400)
        if not _is_int(reorder_level) or reorder_level < 0:
            return _error("reorder_level must be an integer >= 0", 400)

        with lock:
            if sku in inventory:
                return _error("sku already exists", 409)
            inventory[sku] = {
                "sku": sku,
                "name": name.strip(),
                "quantity": quantity,
                "reorder_level": reorder_level,
            }
            return jsonify(inventory[sku]), 201

    def _adjust(sku, direction):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return _error("Request body must be a JSON object", 400)
        quantity = data.get("quantity")
        if not _is_int(quantity) or quantity <= 0:
            return _error("quantity must be a positive integer", 400)

        with lock:
            item = inventory.get(sku)
            if item is None:
                return _error("sku not found", 404)
            if direction == "issue" and quantity > item["quantity"]:
                return _error("insufficient stock", 409)
            item["quantity"] += quantity if direction == "receive" else -quantity
            return jsonify(item), 200

    @app.post("/items/<sku>/receive")
    def receive(sku):
        return _adjust(sku, "receive")

    @app.post("/items/<sku>/issue")
    def issue(sku):
        return _adjust(sku, "issue")

    @app.get("/alerts/low-stock")
    def low_stock():
        with lock:
            low = [i for i in inventory.values() if i["quantity"] <= i["reorder_level"]]
            return jsonify(sorted(low, key=lambda i: i["sku"])), 200

    return app


if __name__ == "__main__":
    # Local development only. In the container, gunicorn serves the app.
    create_app().run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
