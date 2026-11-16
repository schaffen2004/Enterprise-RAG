import uuid
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from src.schemas.storage import S3Config, S3InputFile
from src.utils.config import get_settings
from src.utils.s3 import S3Storage, S3StorageError

DATA_FILE = Path("data") / "test.pdf"


@pytest.fixture
def s3_config() -> S3Config:
    settings = get_settings()
    return S3Config(
        bucket_name=settings.s3_bucket,
        access_key=settings.aws_access_key_id,
        secret_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )


@pytest.fixture
def storage(s3_config: S3Config) -> S3Storage:
    return S3Storage(s3_config)


@pytest.fixture
def s3_key() -> str:
    return f"tests/{uuid.uuid4().hex}-{DATA_FILE.name}"


@pytest.fixture
def input_file(s3_config: S3Config, s3_key: str) -> S3InputFile:
    return S3InputFile(
        file_name=DATA_FILE.name,
        content_type="application/pdf",
        bucket=s3_config.bucket_name,
        key=s3_key,
    )


def test_upload_file(storage: S3Storage, input_file: S3InputFile) -> None:
    content = DATA_FILE.read_bytes()

    key = storage.upload_file(input_file, content)

    assert key == input_file.key
    stored = storage.client.get_object(Bucket=input_file.bucket, Key=key)
    assert stored["Body"].read() == content
    assert stored["ContentType"] == "application/pdf"

    storage.delete_file(key, bucket=input_file.bucket)


def test_delete_file(storage: S3Storage, input_file: S3InputFile) -> None:
    storage.upload_file(input_file, DATA_FILE.read_bytes())

    storage.delete_file(input_file.key, bucket=input_file.bucket)

    with pytest.raises(ClientError):
        storage.client.head_object(Bucket=input_file.bucket, Key=input_file.key)


def test_upload_file_raises_when_bucket_missing(storage: S3Storage) -> None:
    file = S3InputFile(
        file_name=DATA_FILE.name,
        content_type="application/pdf",
        bucket=f"enterprise-rag-missing-bucket-{uuid.uuid4().hex}",
        key=DATA_FILE.name,
    )

    with pytest.raises(S3StorageError):
        storage.upload_file(file, DATA_FILE.read_bytes())


def test_delete_file_raises_when_bucket_missing(storage: S3Storage) -> None:
    with pytest.raises(S3StorageError):
        storage.delete_file(
            DATA_FILE.name,
            bucket=f"enterprise-rag-missing-bucket-{uuid.uuid4().hex}",
        )
