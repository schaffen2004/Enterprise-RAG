import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.model.user import User
from src.services.document_service import DocumentService
from src.utils.config import get_settings
from src.utils.postgres import SessionLocal
from src.utils.s3 import get_s3_storage

DATA_FILE = Path("data") / "test.pdf"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def user_id():
    suffix = uuid.uuid4().hex[:8]
    with SessionLocal() as session:
        user = User(
            username=f"upload_{suffix}",
            email=f"upload_{suffix}@example.com",
            password_hash="not-used-in-this-test",
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        created_id = user.id

    yield created_id

    with SessionLocal() as session:
        user = session.get(User, created_id)
        if user is not None:
            session.delete(user)
            session.commit()


@pytest.fixture
def auth_headers(user_id: UUID) -> dict[str, str]:
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": str(user_id),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


def test_upload_document(client, user_id, auth_headers) -> None:
    content = DATA_FILE.read_bytes()

    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": (DATA_FILE.name, content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == DATA_FILE.name
    assert body["status"] == "uploaded"
    assert body["path"].startswith(f"documents/{user_id}/")

    with SessionLocal() as session:
        document = DocumentService(session).get_by_id(UUID(body["doc_id"]))
        assert document is not None
        assert document.path == body["path"]
        assert document.user_id == user_id

    stored = get_s3_storage().client.get_object(
        Bucket=get_settings().s3_bucket, Key=body["path"]
    )
    assert stored["Body"].read() == content
    assert stored["ContentType"] == "application/pdf"

    get_s3_storage().delete_file(body["path"])


def test_upload_requires_authentication(client) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": (DATA_FILE.name, DATA_FILE.read_bytes(), "application/pdf")},
    )

    assert response.status_code == 401


def test_upload_rejects_unsupported_file_type(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("malware.exe", b"MZ", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_upload_rejects_empty_file(client, auth_headers) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": (DATA_FILE.name, b"", "application/pdf")},
    )

    assert response.status_code == 400
