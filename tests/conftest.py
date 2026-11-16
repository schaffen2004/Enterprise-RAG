import uuid

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.user_service import UserService
from src.utils.postgres import SessionLocal


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def user_data():
    suffix = uuid.uuid4().hex[:8]
    data = {
        "username": f"test_{suffix}",
        "email": f"{suffix}@example.com",
        "password": "StrongPass123",
    }
    yield data

    with SessionLocal() as session:
        service = UserService(session)
        user = service.get_by_username(data["username"])
        if user is not None:
            service.delete(user.id)
