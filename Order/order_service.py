from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG = "http://catalog:5001"


@app.route("/purchase/<int:item_id>")
def purchase(item_id):

    r = requests.get(f"{CATALOG}/info/{item_id}")
    book = r.json()

    if int(book["quantity"]) <= 0:
        return jsonify({"message": "out of stock"})

    requests.get(f"{CATALOG}/purchase/{item_id}")

    return jsonify({"message": "purchase successful"})


app.run(host="0.0.0.0", port=5002)