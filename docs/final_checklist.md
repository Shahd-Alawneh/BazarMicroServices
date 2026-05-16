# Final Submission Checklist

Before submitting, run:

```bash
docker compose up --build
python scripts/client_demo.py
python scripts/performance_test.py --rounds 20
```

Then copy the generated values from `docs/performance_data.csv` into `docs/performance_results.md`.

Recommended final Postman checks:

1. `GET /info/2` twice: first response should be `cache: miss`, second should be `cache: hit`.
2. `POST /purchase/2`.
3. `GET /info/2` again: should become `cache: miss` after invalidation.
4. Compare `GET http://localhost:5001/info/2` and `GET http://localhost:5003/info/2`: quantities should match.
5. Compare `GET http://localhost:5002/orders` and `GET http://localhost:5004/orders`: replicated order logs should include the same purchase records.
