from flask import Flask, jsonify
import csv
import os
import threading
from datetime import datetime
import requests

app = Flask(__name__)

REPLICA_NAME = os.environ.get("REPLICA_NAME", "order")
ORDER_LOG = os.environ.get("ORDER_LOG", "/data/orders.csv")
CATALOG_WRITE_URL = os.environ.get("CATALOG_WRITE_URL", "http://catalog1:5001")

log_lock = threading.Lock()
FIELDNAMES = ["order_id", "item_id", "title", "timestamp", "served_by"]


def init_order_log():
    if not os.path.exists(ORDER_LOG):
        with open(ORDER_LOG, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_orders():
    init_order_log()
    with open(ORDER_LOG, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def save_order(item_id, title):
    with log_lock:
        orders = read_orders()
        next_id = len(orders) + 1
        row = {
            "order_id": next_id,
            "item_id": item_id,
            "title": title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "served_by": REPLICA_NAME,
        }
        orders.append(row)
        with open(ORDER_LOG, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(orders)
        return row


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": REPLICA_NAME})


@app.route("/purchase/<int:item_id>", methods=["POST"])
def purchase(item_id):
    try:
        info_response = requests.get(f"{CATALOG_WRITE_URL}/info/{item_id}", timeout=5)
    except requests.RequestException:
        return jsonify({"error": "catalog service unavailable", "served_by": REPLICA_NAME}), 503

    if info_response.status_code != 200:
        return jsonify(info_response.json()), info_response.status_code

    book = info_response.json()
    if int(book.get("quantity", 0)) <= 0:
        return jsonify({"error": "out of stock", "served_by": REPLICA_NAME}), 400

    try:
        update_response = requests.post(
            f"{CATALOG_WRITE_URL}/update/{item_id}",
            json={"action": "decrement"},
            timeout=8,
        )
    except requests.RequestException:
        return jsonify({"error": "catalog update unavailable", "served_by": REPLICA_NAME}), 503

    if update_response.status_code != 200:
        return jsonify(update_response.json()), update_response.status_code

    order = save_order(item_id, book["title"])
    print(f"[{REPLICA_NAME}] bought book '{book['title']}' | order_id={order['order_id']}")

    return jsonify({
        "message": "purchase successful",
        "order": order,
        "catalog_update": update_response.json(),
        "served_by": REPLICA_NAME,
    })


@app.route("/orders", methods=["GET"])
def list_orders():
    return jsonify(read_orders())


if __name__ == "__main__":
    init_order_log()
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
