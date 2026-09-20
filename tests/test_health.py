from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_test_endpoint():
    response = client.post(
        "/endpoints",
        json={
            "name": "Test Service",
            "url": "https://example.com",
        },
    )

    return response.json()["id"]


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_endpoint():
    response = client.post(
        "/endpoints",
        json={
            "name": "Test Service",
            "url": "https://example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Service"
    assert data["url"] == "https://example.com/"
    assert "id" in data
    assert "created_at" in data


def test_get_endpoints():
    create_test_endpoint()

    response = client.get("/endpoints")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Test Service"


def test_duplicate_endpoint_returns_409():
    endpoint = {
        "name": "Test Service",
        "url": "https://example.com",
    }

    first_response = client.post(
        "/endpoints",
        json=endpoint,
    )

    second_response = client.post(
        "/endpoints",
        json=endpoint,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Endpoint is already registered."
    }


def test_invalid_url_returns_422():
    response = client.post(
        "/endpoints",
        json={
            "name": "Broken Service",
            "url": "not-a-valid-url",
        },
    )

    assert response.status_code == 422


def test_missing_endpoint_returns_404():
    response = client.get("/endpoints/999/checks")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Endpoint not found."
    }


def test_stats_without_checks():
    endpoint_id = create_test_endpoint()

    response = client.get(
        f"/endpoints/{endpoint_id}/stats"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_checks"] == 0
    assert data["successful_checks"] == 0
    assert data["failed_checks"] == 0
    assert data["uptime_percentage"] == 0.0
    assert data["average_response_time_ms"] == 0.0
    assert data["latest_status"] is None


@patch("app.monitor.httpx.get")
def test_successful_endpoint_check(mock_get):
    mock_get.return_value = httpx.Response(
        status_code=200,
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    endpoint_id = create_test_endpoint()

    response = client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["endpoint_id"] == endpoint_id
    assert data["status"] == "healthy"
    assert data["status_code"] == 200
    assert data["error"] is None
    assert data["response_time_ms"] >= 0


@patch("app.monitor.httpx.get")
def test_unhealthy_endpoint_check(mock_get):
    mock_get.return_value = httpx.Response(
        status_code=500,
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    endpoint_id = create_test_endpoint()

    response = client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "unhealthy"
    assert data["status_code"] == 500
    assert data["error"] is None


@patch("app.monitor.httpx.get")
def test_failed_request_is_unhealthy(mock_get):
    mock_get.side_effect = httpx.ConnectError(
        "Connection failed",
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    endpoint_id = create_test_endpoint()

    response = client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "unhealthy"
    assert data["status_code"] is None
    assert data["error"] is not None


@patch("app.monitor.httpx.get")
def test_check_is_saved_to_history(mock_get):
    mock_get.return_value = httpx.Response(
        status_code=200,
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    endpoint_id = create_test_endpoint()

    client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    response = client.get(
        f"/endpoints/{endpoint_id}/checks"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["status"] == "healthy"
    assert data[0]["status_code"] == 200


@patch("app.monitor.httpx.get")
def test_stats_calculation(mock_get):
    endpoint_id = create_test_endpoint()

    mock_get.return_value = httpx.Response(
        status_code=200,
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    mock_get.return_value = httpx.Response(
        status_code=500,
        request=httpx.Request(
            "GET",
            "https://example.com/",
        ),
    )

    client.post(
        f"/endpoints/{endpoint_id}/check"
    )

    response = client.get(
        f"/endpoints/{endpoint_id}/stats"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_checks"] == 3
    assert data["successful_checks"] == 2
    assert data["failed_checks"] == 1
    assert data["uptime_percentage"] == 66.67
    assert data["latest_status"] == "unhealthy"
    assert data["average_response_time_ms"] >= 0