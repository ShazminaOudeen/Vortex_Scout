import pytest
from fastapi.testclient import TestClient

from app.agent import gemini_client
from app.core import store
from main import app
from tests.fake_supabase import FakeSupabase


@pytest.fixture(autouse=True)
def _never_touch_real_supabase(monkeypatch):
    """A developer's backend/.env may hold real keys, and store.reset() deletes rows. Tests must
    never reach a live project: they run on the in-memory store or on FakeSupabase."""
    monkeypatch.setattr(store, "get_supabase", lambda: None)


@pytest.fixture(autouse=True)
def _never_call_real_gemini(monkeypatch):
    """A developer's backend/.env may hold a real GEMINI_API_KEY. Tests must not call Google: it is slow
    (retries on 503), burns free-tier quota and makes the briefing text vary between runs. With the LLM
    step stubbed out, build_checklist() falls back to the deterministic template briefing."""
    monkeypatch.setattr(gemini_client, "_llm_briefing", lambda items: "")


@pytest.fixture(params=["memory", "supabase_fake"])
def backend(request, monkeypatch):
    """Runs the test once against the in-memory store and once through the Supabase code paths."""
    fake = None
    if request.param == "supabase_fake":
        fake = FakeSupabase()
        monkeypatch.setattr(store, "get_supabase", lambda: fake)
    store.reset()
    return fake


@pytest.fixture
def client(backend):
    return TestClient(app)
