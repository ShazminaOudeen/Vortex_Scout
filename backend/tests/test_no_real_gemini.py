from types import SimpleNamespace

from app.agent import gemini_client


def test_tests_never_reach_the_real_gemini_api_even_when_a_key_is_configured(client, monkeypatch):
    calls = []

    def boom(*a, **k):
        calls.append(1)
        raise AssertionError("a test tried to call the real Gemini API")

    monkeypatch.setattr(gemini_client, "get_settings",
                        lambda: SimpleNamespace(gemini_api_key="a-real-looking-key", gemini_model="m"))
    monkeypatch.setattr(gemini_client, "genai", SimpleNamespace(Client=boom))
    r = client.get("/api/v1/agent/checklist")
    assert r.status_code == 200 and r.json()["briefing"].startswith("Good morning!")
    assert calls == []
