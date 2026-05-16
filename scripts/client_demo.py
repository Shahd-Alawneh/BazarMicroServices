import json
import requests

BASE = "http://localhost:5000"


def show(title, method, path):
    print("\n" + "=" * 70)
    print(title)
    response = requests.request(method, BASE + path, timeout=10)
    print(f"{method} {path} -> HTTP {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    show("Search for distributed systems books", "GET", "/search/distributed%20systems")
    show("First info request for book 2: cache miss", "GET", "/info/2")
    show("Second info request for book 2: cache hit", "GET", "/info/2")
    show("Purchase book 2: order replica + catalog update + invalidation", "POST", "/purchase/2")
    show("Info after purchase: cache miss and updated quantity", "GET", "/info/2")
    show("Cache statistics", "GET", "/cache/stats")
