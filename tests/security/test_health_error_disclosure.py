"""Health probes must not expose infrastructure exception details."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from alphapulse.api.database import get_db
from alphapulse.api.routes.health import router


def test_detailed_health_hides_database_exception_details():
    app = FastAPI()
    app.include_router(router)

    class BrokenSession:
        def execute(self, _statement):
            raise RuntimeError("postgresql://admin:secret@db.internal/prod")

    def broken_db():
        yield BrokenSession()

    app.dependency_overrides[get_db] = broken_db
    with TestClient(app) as client:
        response = client.get("/health/detailed")

    assert response.status_code == 200
    body = response.json()
    assert body["components"]["database"] == "unhealthy"
    assert body["message"].endswith("Database connection failed")
    assert "secret" not in response.text
    assert "db.internal" not in response.text
