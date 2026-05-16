from flask import Flask, jsonify
from collections import OrderedDict
import os
import threading
import time
import requests

app = Flask(__name__)

CATALOG_REPLICAS = [url.strip() for url in os.environ.get(
    "CATALOG_REPLICAS", "http://catalog1:5001,http://catalog2:5001"
).split(",") if url.strip()]
ORDER_REPLICAS = [url.strip() for url in os.environ.get(
    "ORDER_REPLICAS", "http://order1:5002,http://order2:5002"
).split(",") if url.strip()]

CACHE_LIMIT = int(os.environ.get("CACHE_LIMIT", "10"))
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "120"))

cache_lock = threading.Lock()
lb_lock = threading.Lock()
info_cache = OrderedDict()
next_catalog = 0
next_order = 0
stats = {"hits": 0, "misses": 0, "invalidations": 0}


def choose_replica(replicas, pointer_name):
    global next_catalog, next_order
    with lb_lock:
        if pointer_name == "catalog":
            url = replicas[next_catalog % len(replicas)]
            next_catalog += 1
        else:
            url = replicas[next_order % len(replicas)]
            next_order += 1
        return url


def get_cached_info(item_id):
    with cache_lock:
        cached = info_cache.get(item_id)
        if not cached:
            stats["misses"] += 1
            return None

        age = time.time() - cached["stored_at"]
        if age > CACHE_TTL_SECONDS:
            info_cache.pop(item_id, None)
            stats["misses"] += 1
            return None

        info_cache.move_to_end(item_id)
        stats["hits"] += 1
        result = dict(cached["data"])
        result["cache"] = "hit"
        return result


def save_cached_info(item_id, data):
    with cache_lock:
        entry = dict(data)
        entry["cache"] = "miss"
        info_cache[item_id] = {"data": entry, "stored_at": time.time()}
        info_cache.move_to_end(item_id)
        while len(info_cache) > CACHE_LIMIT:
            info_cache.popitem(last=False)


def fetch_info_from_catalog(item_id):
    replica = choose_replica(CATALOG_REPLICAS, "catalog")
    response = requests.get(f"{replica}/info/{item_id}", timeout=5)
    return response, replica


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "frontend"})


@app.route("/search/<topic>", methods=["GET"])
def search(topic):
    replica = choose_replica(CATALOG_REPLICAS, "catalog")
    try:
        response = requests.get(f"{replica}/search/{topic}", timeout=5)
        payload = response.json()
        return jsonify({"cache": "not-used-for-search", "forwarded_to": replica, "result": payload}), response.status_code
    except requests.RequestException:
        return jsonify({"error": "catalog service unavailable"}), 503


@app.route("/info/<int:item_id>", methods=["GET"])
def info(item_id):
    cached = get_cached_info(item_id)
    if cached:
        return jsonify(cached)

    try:
        response, replica = fetch_info_from_catalog(item_id)
    except requests.RequestException:
        return jsonify({"error": "catalog service unavailable"}), 503

    payload = response.json()
    if response.status_code == 200:
        payload["forwarded_to"] = replica
        save_cached_info(item_id, payload)
        cached_payload = dict(payload)
        cached_payload["cache"] = "miss"
        return jsonify(cached_payload)
    return jsonify(payload), response.status_code


@app.route("/nocache/info/<int:item_id>", methods=["GET"])
def info_without_cache(item_id):
    try:
        response, replica = fetch_info_from_catalog(item_id)
        payload = response.json()
        if response.status_code == 200:
            payload["cache"] = "bypassed"
            payload["forwarded_to"] = replica
        return jsonify(payload), response.status_code
    except requests.RequestException:
        return jsonify({"error": "catalog service unavailable"}), 503


@app.route("/purchase/<int:item_id>", methods=["POST"])
def purchase(item_id):
    replica = choose_replica(ORDER_REPLICAS, "order")
    try:
        response = requests.post(f"{replica}/purchase/{item_id}", timeout=10)
        payload = response.json()
        payload["forwarded_to"] = replica
        return jsonify(payload), response.status_code
    except requests.RequestException:
        return jsonify({"error": "order service unavailable"}), 503


@app.route("/cache/invalidate/<int:item_id>", methods=["POST"])
def invalidate(item_id):
    with cache_lock:
        removed = info_cache.pop(item_id, None) is not None
        stats["invalidations"] += 1
    print(f"[frontend] invalidate item {item_id}; removed={removed}")
    return jsonify({"message": "cache invalidation processed", "item_id": item_id, "removed": removed})


@app.route("/cache/stats", methods=["GET"])
def cache_stats():
    with cache_lock:
        keys = list(info_cache.keys())
        current_stats = dict(stats)
    return jsonify({"cache_keys": keys, "stats": current_stats, "limit": CACHE_LIMIT, "ttl_seconds": CACHE_TTL_SECONDS})


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    with cache_lock:
        info_cache.clear()
        stats["hits"] = 0
        stats["misses"] = 0
        stats["invalidations"] = 0
    return jsonify({"message": "cache cleared"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
