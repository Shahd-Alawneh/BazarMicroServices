from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG = "http://catalog:5001"
ORDER   = "http://order:5002"

@app.route("/search/<topic>")
def search(topic):
    try:
        r = requests.get(f"{CATALOG}/search/{topic}", timeout=5)
        return jsonify(r.json()), r.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "catalog service unavailable"}), 503


@app.route("/info/<int:item_id>")
def info(item_id):
    try:
        r = requests.get(f"{CATALOG}/info/{item_id}", timeout=5)
        return jsonify(r.json()), r.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "catalog service unavailable"}), 503


@app.route("/purchase/<int:item_id>", methods=["POST"])
def purchase(item_id):
    try:
        r = requests.post(f"{ORDER}/purchase/{item_id}", timeout=5)
        return jsonify(r.json()), r.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "order service unavailable"}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)