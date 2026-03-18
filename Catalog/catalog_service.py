from flask import Flask, jsonify, request
import csv
import threading

app = Flask(__name__)

FILE = "/data/catalog.csv"

lock = threading.Lock()


def read_catalog():
    books = []
    with open(FILE, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            books.append(row)
    return books


def write_catalog(books):
    with open(FILE, "w", newline='') as f:
        fieldnames = ["id", "title", "topic", "price", "quantity"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for b in books:
            writer.writerow(b)


# ✅ query by subject
@app.route("/search/<topic>")
def search(topic):
    books = read_catalog()
    result = []
    for b in books:
        if b["topic"].lower() == topic.lower():
            result.append({
                "id": int(b["id"]),
                "title": b["title"]
            })
    if not result:
        return jsonify({"error": "no books found for this topic"}), 404
    return jsonify(result)


# ✅ query by item
@app.route("/info/<int:item_id>")
def info(item_id):
    books = read_catalog()
    for b in books:
        if int(b["id"]) == item_id:
            return jsonify({
                "title": b["title"],
                "quantity": int(b["quantity"]),
                "price": float(b["price"])
            })
    return jsonify({"error": "item not found"}), 404


# ✅ FIX 3: endpoint مسمى /update بدل /purchase، ويستقبل POST
# يُستخدم داخليًا من Order Server فقط لتخفيض الكمية
@app.route("/update/<int:item_id>", methods=["POST"])
def update(item_id):
    data = request.get_json(silent=True) or {}
    action = data.get("action", "decrement")   # decrement | set_price
    
    with lock:
        books = read_catalog()
        for b in books:
            if int(b["id"]) == item_id:
                if action == "decrement":
                    if int(b["quantity"]) <= 0:
                        return jsonify({"error": "out of stock"}), 400
                    b["quantity"] = str(int(b["quantity"]) - 1)
                    write_catalog(books)
                    return jsonify({"message": "stock updated", "quantity": int(b["quantity"])})
                
                elif action == "set_price":
                    new_price = data.get("price")
                    if new_price is None:
                        return jsonify({"error": "price required"}), 400
                    b["price"] = str(new_price)
                    write_catalog(books)
                    return jsonify({"message": "price updated", "price": new_price})
                
                else:
                    return jsonify({"error": "unknown action"}), 400
        
        return jsonify({"error": "item not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
