# Lab 2 Output Examples

The following output is expected after running:

```bash
docker compose up --build
python scripts/client_demo.py
```

## 1. Search Request

Request:

```http
GET http://localhost:5000/search/distributed%20systems
```

Sample output:

```json
{
  "cache": "not-used-for-search",
  "forwarded_to": "http://catalog1:5001",
  "result": [
    {
      "id": 1,
      "served_by": "catalog1",
      "title": "How to get a good grade in DOS in 40 minutes a day"
    },
    {
      "id": 2,
      "served_by": "catalog1",
      "title": "RPCs for Noobs"
    },
    {
      "id": 5,
      "served_by": "catalog1",
      "title": "How to finish Project 3 on time"
    }
  ]
}
```

## 2. First Info Request: Cache Miss

Request:

```http
GET http://localhost:5000/info/2
```

Sample output:

```json
{
  "cache": "miss",
  "forwarded_to": "http://catalog2:5001",
  "id": 2,
  "price": 40.0,
  "quantity": 5,
  "served_by": "catalog2",
  "title": "RPCs for Noobs",
  "topic": "distributed systems"
}
```

## 3. Second Info Request: Cache Hit

Request:

```http
GET http://localhost:5000/info/2
```

Sample output:

```json
{
  "cache": "hit",
  "forwarded_to": "http://catalog2:5001",
  "id": 2,
  "price": 40.0,
  "quantity": 5,
  "served_by": "catalog2",
  "title": "RPCs for Noobs",
  "topic": "distributed systems"
}
```

## 4. Purchase Request

Request:

```http
POST http://localhost:5000/purchase/2
```

Sample output:

```json
{
  "message": "purchase successful",
  "forwarded_to": "http://order1:5002",
  "served_by": "order1",
  "order": {
    "order_id": 1,
    "item_id": 2,
    "title": "RPCs for Noobs",
    "timestamp": "2026-05-07 10:00:00",
    "served_by": "order1"
  }
}
```

Console log example:

```text
[frontend] invalidate item 2; removed=True
[catalog1] cache invalidated for item 2
[catalog2] replicated update for item 2 using action=decrement
[catalog1] updated item 2 using action=decrement
[order1] bought book 'RPCs for Noobs' | order_id=1
```

## 5. Info Request After Purchase

Because the purchase invalidated the cache, the next info request becomes a cache miss and reads the updated quantity.

```json
{
  "cache": "miss",
  "id": 2,
  "price": 40.0,
  "quantity": 4,
  "title": "RPCs for Noobs"
}
```

## 6. Cache Statistics

Request:

```http
GET http://localhost:5000/cache/stats
```

Sample output:

```json
{
  "cache_keys": [2],
  "limit": 10,
  "stats": {
    "hits": 1,
    "invalidations": 1,
    "misses": 2
  },
  "ttl_seconds": 120
}
```
