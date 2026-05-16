# Lab 2 Performance Results

## Goal

The purpose of this experiment is to compare the average response time of the system with and without caching, and to show the overhead of cache consistency after a write operation.

## How the Measurements Are Collected

Run the project:

```bash
docker compose up --build
```

Then run:

```bash
python scripts/performance_test.py --rounds 20
```

The script measures:

1. `GET /nocache/info/2` to measure response time without caching.
2. `GET /info/2` for the first cached request, which is a cache miss.
3. Repeated `GET /info/2` requests, which become cache hits.
4. `POST /purchase/2`, which triggers cache invalidation and catalog replication.
5. The next `GET /info/2` after the purchase, which becomes a cache miss again.

## Results Table Template

Copy the real results from `docs/performance_data.csv` after running the experiment on your machine.

| Experiment | Requests | Average ms | Min ms | Max ms | Explanation |
|---|---:|---:|---:|---:|---|
| info without cache | 20 | fill from CSV | fill from CSV | fill from CSV | Every request goes to a catalog replica. |
| first cached info request | 1 | fill from CSV | fill from CSV | fill from CSV | First lookup is a miss and stores the value. |
| repeated cached info requests | 20 | fill from CSV | fill from CSV | fill from CSV | Most requests are served directly from frontend memory. |
| purchase with cache invalidation | 1 | fill from CSV | fill from CSV | fill from CSV | Includes order processing, cache invalidation, catalog write, and replication. |
| info after invalidation | 1 | fill from CSV | fill from CSV | fill from CSV | The stale entry was removed, so this request reads from catalog again. |

## Expected Conclusion

Caching should reduce the average latency of repeated `info` requests because the front-end can answer from local memory instead of making an HTTP call to a catalog replica. The purchase request is expected to be slower than a simple cached read because it performs a write, invalidates the cache, and synchronizes the catalog replica.
