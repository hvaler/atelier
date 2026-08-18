"""Unit test for health check endpoint."""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check_returns_healthy():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "atelier-agent"
    assert "version" in data
    assert "gcp_project" in data


def test_root_returns_links():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "/api/health" in data["health_url"]
