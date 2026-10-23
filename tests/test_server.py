
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    """The health endpoint should return a healthy status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_home_endpoint():
    """The home endpoint should respond successfully."""
    response = client.get("/")

    assert response.status_code == 200


def test_protected_invoice_endpoint_requires_authentication():
    """Invoice access should require a valid access token."""
    response = client.get("/invoices/")

    assert response.status_code in (401, 403)
