from flask import Flask, jsonify, request
import csv
import os
import threading
import requests

app = Flask(__name__)

CATALOG_FILE = os.environ.get("CATALOG_FILE", "/data/catalog.csv")
REPLICA_NAME = os.environ.get("REPLICA_NAME", "catalog")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://frontend:5000")
PEER_URLS = [url.strip() for url in os.environ.get("PEER_URLS", "").split(",") if url.strip()]

file_lock = threading.Lock()
FIELDNAMES = ["id", "title", "topic", "price", "quantity"]


def read_catalog():
    with open(CATALOG_FILE, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_catalog(books):
    with open(CATALOG_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(books)


def public_book(row):
    return {
        "id": int(row["id"]),
        "title": row["title"],
        "topic": row["topic"],
        "price": float(row["price"]),
        "quantity": int(row["quantity"]),
        "served_by": REPLICA_NAME,
    }


def invalidate_frontend_cache(item_id):
    try:
        requests.post(f"{FRONTEND_URL}/cache/invalidate/{item_id}", timeout=2)
        print(f"[{REPLICA_NAME}] cache invalidated for item {item_id}")
    except requests.RequestException as exc:
        print(f"[{REPLICA_NAME}] cache invalidation warning for item {item_id}: {exc}")


def apply_update(item_id, action, value=None):
    books = read_catalog()
    for book in books:
        if int(book["id"]) == item_id:
            if action == "decrement":
                current_quantity = int(book["quantity"])
                if current_quantity <= 0:
                    return None, (jsonify({"error": "out of stock", "served_by": REPLICA_NAME}), 400)
                book["quantity"] = str(current_quantity - 1)
            elif action == "increment":
                amount = int(value if value is not None else 1)
                book["quantity"] = str(int(book["quantity"]) + amount)
            elif action == "set_quantity":
                if value is None:
                    return None, (jsonify({"error": "quantity value is required"}), 400)
                book["quantity"] = str(int(value))
            elif action == "set_price":
                if value is None:
                    return None, (jsonify({"error": "price value is required"}), 400)
                book["price"] = str(float(value))
            else:
                return None, (jsonify({"error": "unknown update action"}), 400)

            write_catalog(books)
            return public_book(book), None

    return None, (jsonify({"error": "item not found", "served_by": REPLICA_NAME}), 404)


def replicate_update(item_id, payload):
    replica_reports = []
    for peer in PEER_URLS:
        try:
            response = requests.post(f"{peer}/replica/update/{item_id}", json=payload, timeout=3)
            replica_reports.append({"peer": peer, "status": response.status_code})
        except requests.RequestException as exc:
            replica_reports.append({"peer": peer, "status": "failed", "error": str(exc)})
    return replica_reports


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": REPLICA_NAME})


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    books = read_catalog()
    matches = []
    for book in books:
        if book["topic"].lower() == topic.lower():
            matches.append({"id": int(book["id"]), "title": book["title"], "served_by": REPLICA_NAME})
    if not matches:
        return jsonify({"error": "no books found for this topic", "served_by": REPLICA_NAME}), 404
    return jsonify(matches)


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    books = read_catalog()
    for book in books:
        if int(book["id"]) == item_id:
            return jsonify(public_book(book))
    return jsonify({"error": "item not found", "served_by": REPLICA_NAME}), 404


@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action", "decrement")
    value = data.get("value", data.get("price", data.get("quantity")))

    with file_lock:
        invalidate_frontend_cache(item_id)
        updated_book, error_response = apply_update(item_id, action, value)
        if error_response:
            return error_response

        replication_payload = {"action": action, "value": value}
        replication_report = replicate_update(item_id, replication_payload)

    print(f"[{REPLICA_NAME}] updated item {item_id} using action={action}")
    return jsonify({
        "message": "catalog updated",
        "item": updated_book,
        "replication": replication_report,
        "served_by": REPLICA_NAME,
    })


@app.route("/replica/update/<int:item_id>", methods=["POST"])
def replica_update(item_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action", "decrement")
    value = data.get("value", data.get("price", data.get("quantity")))

    with file_lock:
        updated_book, error_response = apply_update(item_id, action, value)
        if error_response:
            return error_response

    print(f"[{REPLICA_NAME}] replicated update for item {item_id} using action={action}")
    return jsonify({"message": "replica synchronized", "item": updated_book, "served_by": REPLICA_NAME})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
