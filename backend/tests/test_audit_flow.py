import pytest

from app.core import store


def anomaly_for(client, sku_id="s1"):
    return next(a for a in client.get("/api/v1/anomalies").json() if a["sku_id"] == sku_id)


def reconcile(client, anomaly_id, action, **extra):
    return client.post("/api/v1/audit/reconcile", json={"anomaly_id": anomaly_id, "action": action, **extra})


def ledger(sku_id="s1"):
    return store.get_sku(sku_id).ledger_stock


def test_checklist_groups_by_aisle(client):
    data = client.get("/api/v1/agent/checklist").json()
    assert [g["aisle"] for g in data["groups"]] == ["03", "05"]


def test_reconcile_resolves_item(client):
    a = anomaly_for(client)
    r = reconcile(client, a["id"], "restocked", associate="Nimal")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "already_resolved": False, "status": "restocked",
                        "ledger_stock": 70, "ledger_adjustment": 0}
    after = anomaly_for(client)
    assert after["status"] == "restocked" and after["resolved_at"] is not None


def test_reconcile_writes_one_audit_row(client):
    a = anomaly_for(client)
    reconcile(client, a["id"], "restocked", associate="Nimal", units=24)
    log = store.list_audit()
    assert len(log) == 1
    assert (log[0]["anomaly_id"], log[0]["action"], log[0]["associate"], log[0]["units"]) == (
        a["id"], "restocked", "Nimal", 24)


def test_restocked_and_false_alarm_leave_the_ledger_alone(client):
    reconcile(client, anomaly_for(client, "s1")["id"], "restocked", units=24)
    reconcile(client, anomaly_for(client, "s2")["id"], "false_alarm", units=5)
    assert (ledger("s1"), ledger("s2")) == (70, 32)


def test_damaged_writes_off_units_from_the_ledger(client):
    r = reconcile(client, anomaly_for(client)["id"], "damaged", units=12)
    assert r.json()["ledger_adjustment"] == -12 and r.json()["ledger_stock"] == 58
    assert ledger() == 58


def test_damaged_never_takes_the_ledger_below_zero(client):
    reconcile(client, anomaly_for(client)["id"], "damaged", units=9999)
    assert ledger() == 0


def test_damaged_without_units_changes_nothing(client):
    r = reconcile(client, anomaly_for(client)["id"], "damaged")
    assert r.json()["ledger_adjustment"] == 0 and ledger() == 70


def test_double_reconcile_is_idempotent(client):
    a = anomaly_for(client)
    first = reconcile(client, a["id"], "damaged", units=10, associate="Nimal")
    second = reconcile(client, a["id"], "damaged", units=10, associate="Nimal")
    assert first.json()["already_resolved"] is False
    assert second.status_code == 200
    assert second.json()["already_resolved"] is True and second.json()["status"] == "damaged"
    assert second.json()["ledger_adjustment"] == 0
    assert ledger() == 60                       # written off once, not twice
    assert len(store.list_audit()) == 1         # one audit row, not two


def test_second_tap_with_a_different_action_does_not_overwrite(client):
    a = anomaly_for(client)
    reconcile(client, a["id"], "restocked")
    r = reconcile(client, a["id"], "false_alarm")
    assert r.json()["already_resolved"] is True and r.json()["status"] == "restocked"
    assert anomaly_for(client)["status"] == "restocked"
    assert [x["action"] for x in store.list_audit()] == ["restocked"]


def test_reconcile_unknown_id(client):
    assert reconcile(client, "nope", "damaged").status_code == 404
    assert store.list_audit() == []


def test_reconcile_validates_payload(client):
    a = anomaly_for(client)
    assert reconcile(client, a["id"], "stolen").status_code == 422
    assert reconcile(client, a["id"], "damaged", units=-1).status_code == 422
    assert anomaly_for(client)["status"] == "open"


def test_stats_with_nothing_reconciled(client):
    assert client.get("/api/v1/audit/stats").json() == {
        "total": 0, "restocked": 0, "damaged": 0, "false_alarm": 0, "false_alarm_rate": 0.0}


def test_stats_expose_false_alarm_counts(client):
    for sku, action in [("s1", "restocked"), ("s2", "false_alarm"), ("s3", "false_alarm")]:
        reconcile(client, anomaly_for(client, sku)["id"], action)
    s = client.get("/api/v1/audit/stats").json()
    assert (s["total"], s["restocked"], s["false_alarm"], s["damaged"]) == (3, 1, 2, 0)
    assert s["false_alarm_rate"] == pytest.approx(0.6667, abs=1e-4)


def test_resolved_items_drop_off_the_checklist(client):
    reconcile(client, anomaly_for(client, "s1")["id"], "restocked")
    data = client.get("/api/v1/agent/checklist").json()
    assert [g["aisle"] for g in data["groups"]] == ["05"]
