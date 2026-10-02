def test_checklist_groups_by_aisle(client):
    data = client.get("/api/v1/agent/checklist").json()
    assert [g["aisle"] for g in data["groups"]] == ["03", "05"]


def test_reconcile_resolves_item(client):
    r = client.post("/api/v1/audit/reconcile", json={"anomaly_id": "a1", "action": "restocked"})
    assert r.json() == {"ok": True}
    statuses = {a["id"]: a["status"] for a in client.get("/api/v1/anomalies").json()}
    assert statuses["a1"] == "restocked"


def test_reconcile_unknown_id(client):
    assert client.post("/api/v1/audit/reconcile", json={"anomaly_id": "nope", "action": "damaged"}).status_code == 404
