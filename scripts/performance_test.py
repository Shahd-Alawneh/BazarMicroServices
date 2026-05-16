import argparse
import csv
import statistics
import time
import requests


def measure(base_url, path, rounds, method="GET"):
    latencies = []
    for _ in range(rounds):
        start = time.perf_counter()
        response = requests.request(method, base_url + path, timeout=10)
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)
        response.raise_for_status()
    return latencies


def summarize(name, values):
    return {
        "experiment": name,
        "requests": len(values),
        "average_ms": round(statistics.mean(values), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Measure Bazar Lab 2 response time.")
    parser.add_argument("--base", default="http://localhost:5000")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--out", default="docs/performance_data.csv")
    args = parser.parse_args()

    requests.post(args.base + "/cache/clear", timeout=10)

    no_cache = measure(args.base, "/nocache/info/2", args.rounds)
    requests.post(args.base + "/cache/clear", timeout=10)
    cache_miss_once = measure(args.base, "/info/2", 1)
    cache_hits = measure(args.base, "/info/2", args.rounds)
    purchase = measure(args.base, "/purchase/2", 1, method="POST")
    after_invalidation_miss = measure(args.base, "/info/2", 1)

    rows = [
        summarize("info without cache", no_cache),
        summarize("first cached info request", cache_miss_once),
        summarize("repeated cached info requests", cache_hits),
        summarize("purchase with cache invalidation", purchase),
        summarize("info after invalidation", after_invalidation_miss),
    ]

    with open(args.out, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["experiment", "requests", "average_ms", "min_ms", "max_ms"])
        writer.writeheader()
        writer.writerows(rows)

    print("Performance summary")
    for row in rows:
        print(row)
    print(f"Saved results to {args.out}")
