from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from ..schemas.storage import S3Config, S3InputFile
from .config import get_settings


class S3StorageError(Exception):
    """Raised when an S3 operation fails."""


class S3Storage:
    def __init__(self, config: S3Config) -> None:
        self.config = config
        self.client = boto3.client(
            "s3",
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region_name,
        )

    def upload_file(self, file: S3InputFile, content: bytes) -> str:
        try:
            self.client.put_object(
                Bucket=file.bucket,
                Key=file.key,
                Body=content,
                ContentType=file.content_type,
            )
        except (ClientError, BotoCoreError) as exc:
            raise S3StorageError(
                f"Failed to upload '{file.key}' to bucket '{file.bucket}'"
            ) from exc
        return file.key

    def delete_file(self, key: str, bucket: str | None = None) -> None:
        target_bucket = bucket or self.config.bucket_name
        try:
            self.client.delete_object(Bucket=target_bucket, Key=key)
        except (ClientError, BotoCoreError) as exc:
            raise S3StorageError(
                f"Failed to delete '{key}' from bucket '{target_bucket}'"
            ) from exc


@lru_cache
def get_s3_storage() -> S3Storage:
    settings = get_settings()
    return S3Storage(
        S3Config(
            bucket_name=settings.s3_bucket,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
    )
