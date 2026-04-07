from flask import Flask, jsonify
import requests
import csv
import os
import threading
from datetime import datetime

app = Flask(__name__)

CATALOG = "http://catalog:5001"

ORDER_LOG = "/data/orders.csv"
log_lock = threading.Lock()


def init_order_log():
    """إنشاء ملف الـ orders لو مش موجود"""
    if not os.path.exists(ORDER_LOG):
        with open(ORDER_LOG, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["order_id", "item_id", "title", "timestamp"])
            writer.writeheader()


def save_order(item_id, title):
    """حفظ الطلب في ملف orders.csv"""
    with log_lock:
        orders = []
        try:
            with open(ORDER_LOG, newline='') as f:
                orders = list(csv.DictReader(f))
        except FileNotFoundError:
            pass
        
        new_id = len(orders) + 1
        new_order = {
            "order_id": new_id,
            "item_id": item_id,
            "title": title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        orders.append(new_order)
        
        with open(ORDER_LOG, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["order_id", "item_id", "title", "timestamp"])
            writer.writeheader()
            writer.writerows(orders)
        
        return new_id


@app.route("/purchase/<int:item_id>", methods=["POST"])
def purchase(item_id):
    try:
        r = requests.get(f"{CATALOG}/info/{item_id}", timeout=5)
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "catalog service unavailable"}), 503

    if r.status_code == 404:
        return jsonify({"error": "item not found"}), 404

    book = r.json()

    if book.get("quantity", 0) <= 0:
        return jsonify({"error": "out of stock"}), 400

    try:
        u = requests.post(
            f"{CATALOG}/update/{item_id}",
            json={"action": "decrement"},
            timeout=5
        )
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "catalog service unavailable"}), 503

    if u.status_code != 200:
        return jsonify({"error": u.json().get("error", "update failed")}), 400

    order_id = save_order(item_id, book["title"])

    print(f"[ORDER] bought book '{book['title']}' | order_id={order_id}")

    return jsonify({
        "message": "purchase successful",
        "order_id": order_id,
        "item_id": item_id,
        "title": book["title"]
    })


@app.route("/orders", methods=["GET"])
def list_orders():
    try:
        with open(ORDER_LOG, newline='') as f:
            orders = list(csv.DictReader(f))
        return jsonify(orders)
    except FileNotFoundError:
        return jsonify([])

if __name__ == "__main__":
    init_order_log()
    app.run(host="0.0.0.0", port=5002, debug=False)