from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..model.document import Document
from ..model.user import User
from ..schemas.document import DocumentRead
from ..schemas.storage import S3InputFile
from ..services.document_service import DocumentService, DuplicateDocumentError
from ..utils.config import get_settings
from ..utils.s3 import S3Storage, S3StorageError, get_s3_storage
from .dependencies import get_current_user, get_db

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
}


def build_s3_input_file(
    storage: S3Storage,
    user_id: UUID,
    file_name: str,
    extension: str,
    content_type: str,
) -> S3InputFile:
    key = f"documents/{user_id}/{uuid4().hex}{extension}"
    return S3InputFile(
        file_name=file_name,
        content_type=content_type,
        bucket=storage.config.bucket_name,
        key=key,
    )


@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
    storage: S3Storage = Depends(get_s3_storage),
) -> Document:
    settings = get_settings()

    file_name = Path(file.filename or "").name
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A file name is required",
        )

    extension = Path(file_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read(settings.max_upload_size_bytes + 1)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty",
        )
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_mb} MB limit",
        )

    input_file = build_s3_input_file(
        storage=storage,
        user_id=current_user.id,
        file_name=file_name,
        extension=extension,
        content_type=ALLOWED_EXTENSIONS[extension],
    )

    try:
        storage.upload_file(input_file, content)
    except S3StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload the document to storage",
        ) from exc

    service = DocumentService(session)
    try:
        return service.create(
            user_id=current_user.id,
            name=file_name,
            path=input_file.key,
        )
    except DuplicateDocumentError as exc:
        _delete_stored_object(storage, input_file.key)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with the same storage path already exists",
        ) from exc
    except Exception as exc:
        _delete_stored_object(storage, input_file.key)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata",
        ) from exc


def _delete_stored_object(storage: S3Storage, key: str) -> None:
    try:
        storage.delete_file(key)
    except S3StorageError:
        # Best-effort cleanup: the original error is more useful to the caller.
        pass
