# Lab 2 Design Document: Replication, Caching, and Consistency

## 1. Overview

This version of Bazar.com extends the Lab 1 microservices design. The original system had one front-end service, one catalog service, and one order service. Lab 2 keeps the same REST-based style, but adds replication and caching to reduce read latency and to handle a higher number of requests.

The new system contains five running services:

1. Frontend service
2. Catalog replica 1
3. Catalog replica 2
4. Order replica 1
5. Order replica 2

The front-end service is not replicated. It receives all client requests, checks the cache for `info` requests, and uses a round-robin load balancing policy to forward requests to backend replicas.

## 2. Catalog Expansion

The catalog now includes the original four books from Lab 1 and the three new Lab 2 books:

1. How to finish Project 3 on time
2. Why theory classes are so hard
3. Spring in the Pioneer Valley

The catalog data is stored in two separate CSV files, one per catalog replica:

- `Data/catalog1.csv`
- `Data/catalog2.csv`

Using two files makes the replication behavior visible and easy to inspect.

## 3. Replication Design

### Catalog Replication

There are two catalog replicas. The Docker Compose file starts both replicas from the same source code, but each replica receives different environment variables:

- `REPLICA_NAME`
- `CATALOG_FILE`
- `PEER_URLS`

Catalog writes are handled through `/update/<item_id>`. When a write arrives, the catalog replica first asks the front-end to invalidate the cached item. Then it updates its local CSV file. Finally, it forwards the same update to its peer replica using `/replica/update/<item_id>`.

This keeps both catalog CSV files synchronized after buy operations and manual stock/price updates.

### Order Replication

There are two order replicas. The front-end forwards purchase requests to them using round-robin load balancing. Each order replica writes to its own order log:

- `Data/orders1.csv`
- `Data/orders2.csv`

After a purchase is written locally, the order replica also sends the order record to the peer order replica through the internal endpoint `POST /replica/order`. This keeps both order logs synchronized while still allowing the front-end to distribute purchase requests across `order1` and `order2`.

The order service does not keep catalog data itself. It checks the catalog and asks the catalog service to decrement stock.

## 4. Caching Design

The front-end includes an in-memory cache for `/info/<item_id>` requests. The cache stores recently requested book information, including title, price, quantity, and the catalog replica that served the request.

The cache is useful only for read requests. Purchase and update requests always go to backend services because they modify persistent data.

The cache uses:

- a fixed size limit through `CACHE_LIMIT`,
- a time-to-live through `CACHE_TTL_SECONDS`,
- an `OrderedDict` so older entries can be removed when the cache becomes full.

The first request for a book is a cache miss. The front-end forwards the request to one of the catalog replicas and stores the result. Repeating the same request before invalidation becomes a cache hit.

## 5. Cache Consistency

A stale cache entry would be dangerous after a purchase because the quantity changes. To avoid this, the catalog service uses a server-push invalidation approach.

Before the catalog writes to its CSV file, it sends:

```http
POST /cache/invalidate/<item_id>
```

to the front-end service. The front-end removes that item from the cache. The next `/info/<item_id>` request becomes a cache miss and fetches the fresh value from the catalog.

This provides strong consistency for cached item information in the normal execution path: cached values are removed before the write is committed.

## 6. Load Balancing

The front-end uses round-robin load balancing.

- `/search/<topic>` requests rotate between catalog replicas.
- Cache misses for `/info/<item_id>` rotate between catalog replicas.
- `/purchase/<item_id>` requests rotate between order replicas.

Round-robin was chosen because it is simple, deterministic, and easy to explain during the lab demo.

## 7. REST API Summary

Important frontend endpoints:

- `GET /search/<topic>`
- `GET /info/<item_id>`
- `GET /nocache/info/<item_id>`
- `POST /purchase/<item_id>`
- `GET /cache/stats`
- `POST /cache/clear`

Important catalog endpoints:

- `GET /search/<topic>`
- `GET /info/<item_id>`
- `POST /update/<item_id>`
- `POST /replica/update/<item_id>`

Important order endpoints:

- `POST /purchase/<item_id>`
- `GET /orders`

## 8. Design Tradeoffs

### CSV Instead of a Heavy Database

The lab asks for lightweight persistence. CSV files are enough for this project and make the data easy to inspect. A real production system would use a transactional database.

### In-Memory Cache Inside the Frontend

The cache was implemented inside the front-end process instead of creating a separate cache microservice. This reduces the number of services and avoids extra REST calls between the front-end and a separate cache node.

### Primary Write Path for Catalog Updates

Order replicas send catalog writes to `catalog1`. `catalog1` then replicates the update to `catalog2`. This keeps write behavior simple and avoids conflicting concurrent writes across catalog replicas. Reads can still be load-balanced across both replicas.

## 9. Known Limitations

- If `catalog1` is down, purchases fail because it is the primary write target.
- The system does not implement leader election.
- The system does not use a real distributed consensus protocol.
- Order logs are kept separately per order replica.
- The in-memory cache is lost when the front-end container restarts.

## 10. Possible Improvements

- Add automatic failover if `catalog1` is unavailable.
- Replace CSV files with SQLite to improve local transaction handling.
- Add a background health checker for replicas.
- Add a separate cache service such as Redis.
- Add graphs generated automatically from the performance script output.

## 11. How to Run

Start all containers:

```bash
docker compose up --build
```

Run the demo client:

```bash
python scripts/client_demo.py
```

Run performance measurements:

```bash
python scripts/performance_test.py --rounds 20
```
