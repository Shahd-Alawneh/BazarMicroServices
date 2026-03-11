from flask import Flask, jsonify
import requests

app = Flask(__name__)

CATALOG = "http://catalog:5001"
ORDER = "http://order:5002"


@app.route("/search/<topic>")
def search(topic):

    r = requests.get(f"{CATALOG}/search/{topic}")

    return jsonify(r.json())


@app.route("/info/<int:item_id>")
def info(item_id):

    r = requests.get(f"{CATALOG}/info/{item_id}")

    return jsonify(r.json())


@app.route("/purchase/<int:item_id>")
def purchase(item_id):

    r = requests.get(f"{ORDER}/purchase/{item_id}")

    return jsonify(r.json())


app.run(host="0.0.0.0", port=5000)