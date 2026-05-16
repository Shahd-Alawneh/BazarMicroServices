# Suggested Git Commit Plan for Lab 2

Use this plan so the repository has a healthy number of meaningful commits. After each stage, run the relevant test, commit, and push.

## Stage 1 — Prepare Lab 2 branch and catalog data

```bash
git checkout -b lab2-replication-cache
git add Data/catalog.csv Data/catalog1.csv Data/catalog2.csv Data/orders1.csv Data/orders2.csv
git commit -m "Add Lab 2 catalog data and replica storage files"
git push -u origin lab2-replication-cache
```

## Stage 2 — Add catalog replica configuration

```bash
git add Catalog/catalog_service.py
git commit -m "Add catalog replica configuration and update endpoint"
git push
```

## Stage 3 — Add catalog-to-catalog synchronization

```bash
git add Catalog/catalog_service.py
git commit -m "Synchronize catalog writes across replicas"
git push
```

## Stage 4 — Add order replicas

```bash
git add Order/order_service.py
git commit -m "Support replicated order services with separate logs"
git push
```

## Stage 5 — Add frontend load balancing

```bash
git add Frontend/frontend_service.py
git commit -m "Load balance frontend requests across backend replicas"
git push
```

## Stage 6 — Add frontend cache

```bash
git add Frontend/frontend_service.py
git commit -m "Add in-memory cache for catalog info lookups"
git push
```

## Stage 7 — Add cache invalidation

```bash
git add Frontend/frontend_service.py Catalog/catalog_service.py
git commit -m "Invalidate cached book info before catalog writes"
git push
```

## Stage 8 — Update Docker Compose

```bash
git add docker-compose.yml Catalog/Dockerfile Order/Dockerfile Frontend/Dockerfile
git commit -m "Run Lab 2 services with Docker Compose replicas"
git push
```

## Stage 9 — Add testing scripts

```bash
git add scripts/client_demo.py scripts/performance_test.py
git commit -m "Add demo and performance measurement scripts"
git push
```

## Stage 10 — Add final documentation

```bash
git add README.md docs/design_lab2.md docs/output_lab2.md docs/performance_results.md docs/commit_plan.md
git commit -m "Document Lab 2 design output and performance experiments"
git push
```

## Important Notes

- Do not push everything in one commit.
- Write commit messages that describe the exact change.
- Run `docker compose up --build` after the Docker stage.
- Run `python scripts/client_demo.py` before the final commit.
