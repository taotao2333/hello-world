import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db


@pytest.fixture
def client():
    init_db()
    return TestClient(app)


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "股智先知"


def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "股智先知" in resp.text


def test_predictions_page(client):
    resp = client.get("/predictions")
    assert resp.status_code == 200
    assert "预测" in resp.text


def test_news_page(client):
    resp = client.get("/news")
    assert resp.status_code == 200


def test_review_page(client):
    resp = client.get("/review")
    assert resp.status_code == 200


def test_predictions_api(client):
    resp = client.get("/api/predictions")
    assert resp.status_code == 200
