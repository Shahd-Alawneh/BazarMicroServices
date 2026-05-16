# Bazar.com Lab 2 — Replication, Caching, and Consistency

This repository extends the Lab 1 Bazar.com bookstore into a higher-load version of the system. Lab 2 adds:

- seven catalog books instead of four,
- two catalog replicas,
- two order replicas,
- a front-end round-robin load balancer,
- an in-memory LRU-style cache for `info` lookups,
- cache invalidation before write operations,
- replica-to-replica synchronization for catalog and order writes,
- scripts and documentation for output and performance measurements.

## Architecture

```text
Client
  |
  v
Frontend :5000
  |-- round-robin reads --> Catalog Replica 1 :5001
  |-- round-robin reads --> Catalog Replica 2 :5003
  |-- round-robin buys  --> Order Replica 1   :5002
  |-- round-robin buys  --> Order Replica 2   :5004

Order replicas send writes to catalog1 and replicate their order logs to each other.
Catalog1 invalidates the frontend cache, updates its CSV file, then replicates the update to catalog2.
```

## Services

| Service | Container | Host Port | Internal Port | Responsibility |
|---|---|---:|---:|---|
| Frontend | `bazar-frontend` | 5000 | 5000 | Client API, cache, load balancing |
| Catalog 1 | `bazar-catalog1` | 5001 | 5001 | Catalog read/write replica |
| Catalog 2 | `bazar-catalog2` | 5003 | 5001 | Catalog read replica synchronized by catalog1 |
| Order 1 | `bazar-order1` | 5002 | 5002 | Purchase replica and order-log sync |
| Order 2 | `bazar-order2` | 5004 | 5002 | Purchase replica and order-log sync |

## Data Files

The project still uses lightweight CSV persistence:

```text
Data/catalog1.csv   # catalog replica 1 database
Data/catalog2.csv   # catalog replica 2 database
Data/orders1.csv    # order replica 1 log
Data/orders2.csv    # order replica 2 log
```

## Run the Project

```bash
docker compose up --build
```

Open another terminal and test the front-end API:

```bash
curl http://localhost:5000/search/distributed%20systems
curl http://localhost:5000/info/2
curl http://localhost:5000/info/2
curl -X POST http://localhost:5000/purchase/2
curl http://localhost:5000/info/2
curl http://localhost:5000/cache/stats
```

You can also run the prepared client script:

```bash
python scripts/client_demo.py
```

## Main API Endpoints

### Frontend

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/search/<topic>` | Uses catalog round-robin, no cache |
| GET | `/info/<item_id>` | Uses cache first, then catalog round-robin |
| GET | `/nocache/info/<item_id>` | Bypasses cache for measurements |
| POST | `/purchase/<item_id>` | Uses order round-robin |
| POST | `/cache/invalidate/<item_id>` | Called by catalog before writes |
| GET | `/cache/stats` | Shows hit/miss/invalidation counters |
| POST | `/cache/clear` | Clears the cache before experiments |

### Catalog Replicas

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/search/<topic>` | Query by topic |
| GET | `/info/<item_id>` | Query by item ID |
| POST | `/update/<item_id>` | Write operation, invalidates cache, then replicates |
| POST | `/replica/update/<item_id>` | Internal synchronization endpoint |

Supported update actions:

```json
{ "action": "decrement" }
{ "action": "increment", "value": 3 }
{ "action": "set_price", "value": 45 }
{ "action": "set_quantity", "value": 10 }
```

### Order Replicas

| Method | Endpoint | Notes |
|---|---|---|
| POST | `/purchase/<item_id>` | Checks stock, updates catalog, logs the order |
| GET | `/orders` | Lists local order log for this replica |
| POST | `/replica/order` | Internal order-log synchronization endpoint |

## Performance Measurement

Run the system first, then execute:

```bash
python scripts/performance_test.py --rounds 20
```

The script writes results to:

```text
docs/performance_data.csv
```

Then copy the numbers into `docs/performance_results.md` or include screenshots/plots if required by the instructor.

## Git Commit Plan

Lab 2 should not be pushed as one large commit. A recommended staged workflow is documented in:

```text
docs/commit_plan.md
```

Use one commit per stage, test after each stage, and push after each commit.

## Documentation

```text
docs/design_lab2.md          # design and tradeoffs
docs/output_lab2.md          # sample run output
docs/performance_results.md  # experiment table and explanation
docs/commit_plan.md          # staged Git workflow
```
