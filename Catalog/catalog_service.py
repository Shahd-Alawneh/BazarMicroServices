from flask import Flask, jsonify
import csv

app = Flask(__name__)

FILE = "../data/catalog.csv"


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


@app.route("/search/<topic>")
def search(topic):

    books = read_catalog()
    result = []

    for b in books:
        if b["topic"] == topic:
            result.append({
                "id": b["id"],
                "title": b["title"]
            })

    return jsonify(result)


@app.route("/info/<int:item_id>")
def info(item_id):

    books = read_catalog()

    for b in books:
        if int(b["id"]) == item_id:

            return jsonify({
                "title": b["title"],
                "quantity": b["quantity"],
                "price": b["price"]
            })

    return jsonify({"error": "not found"})


@app.route("/purchase/<int:item_id>")
def purchase(item_id):

    books = read_catalog()

    for b in books:
        if int(b["id"]) == item_id:

            if int(b["quantity"]) <= 0:
                return jsonify({"message": "out of stock"})

            b["quantity"] = str(int(b["quantity"]) - 1)

            write_catalog(books)

            return jsonify({"message": "stock updated"})

    return jsonify({"error": "not found"})


app.run(host="0.0.0.0", port=5001)