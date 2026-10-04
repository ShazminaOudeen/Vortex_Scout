"""The app must run with no Supabase keys (the README promises it) and tests must never reach a live project."""
import importlib

import pytest

from app.core import database, store
from app.core.config import get_settings


@pytest.fixture
def no_keys(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    get_settings.cache_clear()
    database.get_supabase.cache_clear()
    yield
    get_settings.cache_clear()
    database.get_supabase.cache_clear()


def test_get_supabase_is_none_without_keys(no_keys):
    assert database.get_supabase() is None


def test_store_uses_memory_when_there_is_no_client(no_keys, monkeypatch):
    monkeypatch.setattr(store, "get_supabase", database.get_supabase)  # undo the autouse guard
    assert store.using_supabase() is False
    store.reset()
    assert len(store.list_skus()) == 200
    assert store.insert_transactions([{"store_id": "store_01", "sku_id": "s1", "quantity": 1, "unit_price": 395,
                                       "timestamp": __import__("datetime").datetime(2026, 10, 2, 9, 15)}]) == 1
    assert len(store.TRANSACTIONS) == 1                       # it really went to the in-memory store


def test_importing_the_store_never_writes_to_supabase(monkeypatch):
    """store.py populates memory at import time; with keys configured that must not touch the database."""
    class Boom:
        def __getattr__(self, name):
            raise AssertionError("import touched Supabase")

    monkeypatch.setattr(database, "get_supabase", lambda: Boom())
    importlib.reload(store)  # would raise if the import-time bootstrap used the client
    assert len(store.SKUS) == 200


def test_memory_store_is_fully_populated_at_startup():
    store.reset()
    assert {a.sku_id for a in store.list_anomalies()} == {"s1", "s2", "s3"}
    assert store.list_stores() == [{"id": "store_01", "name": "Scout Demo Store (Colombo)"}]
    assert store.get_sku("s1").ledger_stock == 70
