import pytest
from fastapi.testclient import TestClient
from app.main import app, store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def clean_store():
    store.expenses.clear()
    store._id_counter = 1
    yield store
    store.expenses.clear()
    store._id_counter = 1
