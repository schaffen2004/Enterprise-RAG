from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..model.document import Document, DocumentStatus


class DuplicateDocumentError(Exception):
    """Raised when a document with the same storage path already exists."""


class DocumentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, doc_id: UUID) -> Document | None:
        return self.session.get(Document, doc_id)

    def get_by_path(self, path: str) -> Document | None:
        return self.session.scalar(select(Document).where(Document.path == path))

    def list_by_user(self, user_id: UUID) -> list[Document]:
        return list(
            self.session.scalars(
                select(Document)
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
            )
        )

    def create(
        self,
        user_id: UUID,
        name: str,
        path: str,
        status: DocumentStatus = DocumentStatus.PENDING,
    ) -> Document:
        document = Document(
            user_id=user_id,
            name=name,
            path=path,
            status=status,
        )
        try:
            self.session.add(document)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateDocumentError(
                f"Document with path '{path}' already exists"
            ) from exc
        self.session.refresh(document)
        return document

    def delete(self, doc_id: UUID) -> bool:
        document = self.session.get(Document, doc_id)
        if document is None:
            return False
        self.session.delete(document)
        self.session.commit()
        return True
