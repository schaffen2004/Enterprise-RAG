from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..model.document import DocumentStatus


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_id: UUID
    name: str
    path: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
