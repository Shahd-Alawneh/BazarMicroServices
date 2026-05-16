from flask import Flask, jsonify, request
import csv
import os
import threading
from datetime import datetime
import requests

app = Flask(__name__)

REPLICA_NAME = os.environ.get("REPLICA_NAME", "order")
ORDER_LOG = os.environ.get("ORDER_LOG", "/data/orders.csv")
CATALOG_WRITE_URL = os.environ.get("CATALOG_WRITE_URL", "http://catalog1:5001")
PEER_URLS = [url.strip() for url in os.environ.get("PEER_URLS", "").split(",") if url.strip()]

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


def write_orders(orders):
    with open(ORDER_LOG, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(orders)


def append_order(row):
    """Append an order if this exact source order was not already replicated."""
    with log_lock:
        orders = read_orders()
        for existing in orders:
            if (
                str(existing.get("order_id")) == str(row.get("order_id"))
                and existing.get("served_by") == row.get("served_by")
            ):
                return False
        orders.append({
            "order_id": row["order_id"],
            "item_id": row["item_id"],
            "title": row["title"],
            "timestamp": row["timestamp"],
            "served_by": row["served_by"],
        })
        write_orders(orders)
        return True


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
        write_orders(orders)
        return row


def replicate_order(order):
    reports = []
    for peer in PEER_URLS:
        try:
            response = requests.post(f"{peer}/replica/order", json=order, timeout=3)
            reports.append({"peer": peer, "status": response.status_code})
        except requests.RequestException as exc:
            reports.append({"peer": peer, "status": "failed", "error": str(exc)})
    return reports


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
    replication_report = replicate_order(order)
    print(f"[{REPLICA_NAME}] bought book '{book['title']}' | order_id={order['order_id']}")

    return jsonify({
        "message": "purchase successful",
        "order": order,
        "order_replication": replication_report,
        "catalog_update": update_response.json(),
        "served_by": REPLICA_NAME,
    })


@app.route("/replica/order", methods=["POST"])
def replica_order():
    data = request.get_json(silent=True) or {}
    required = {"order_id", "item_id", "title", "timestamp", "served_by"}
    if not required.issubset(data.keys()):
        return jsonify({"error": "invalid replicated order payload", "served_by": REPLICA_NAME}), 400

    inserted = append_order(data)
    print(f"[{REPLICA_NAME}] replicated order from {data['served_by']} | inserted={inserted}")
    return jsonify({"message": "order replica synchronized", "inserted": inserted, "served_by": REPLICA_NAME})


@app.route("/orders", methods=["GET"])
def list_orders():
    return jsonify(read_orders())


if __name__ == "__main__":
    init_order_log()
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
