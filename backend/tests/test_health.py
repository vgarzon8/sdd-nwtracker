from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import get_session
from app.main import app


@pytest.fixture()
def client(session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def broken_client() -> Generator[TestClient, None, None]:
    def _broken_session() -> Generator[MagicMock, None, None]:
        mock = MagicMock()
        mock.exec.side_effect = RuntimeError("DB unavailable")
        yield mock

    app.dependency_overrides[get_session] = _broken_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["version"] != ""


def test_health_ok_response_schema(client: TestClient) -> None:
    body = client.get("/health").json()
    assert set(body.keys()) == {"status", "db", "version"}


def test_health_db_error(broken_client: TestClient) -> None:
    response = broken_client.get("/health")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "error"


def test_health_db_error_no_version(broken_client: TestClient) -> None:
    body = broken_client.get("/health").json()
    assert "version" not in body
