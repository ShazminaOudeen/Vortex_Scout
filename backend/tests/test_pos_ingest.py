def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ingest_batch(client):
    body = {"transactions": [
        {"timestamp": "2026-10-02T09:15:00", "sku_id": "s1", "store_id": "store_01", "quantity": 2, "unit_price": 395}
    ]}
    r = client.post("/api/v1/pos/stream", json=body)
    assert r.status_code == 200 and r.json() == {"ingested": 1}


def test_ingest_rejects_bad_quantity(client):
    body = {"transactions": [
        {"timestamp": "2026-10-02T09:15:00", "sku_id": "s1", "store_id": "store_01", "quantity": 0, "unit_price": 395}
    ]}
    assert client.post("/api/v1/pos/stream", json=body).status_code == 422
