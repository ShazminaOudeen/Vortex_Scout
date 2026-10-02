import pytest
from fastapi.testclient import TestClient

from app.core import store
from main import app


@pytest.fixture
def client():
    store.reset()
    return TestClient(app)
