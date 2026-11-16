from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from ..model.user import User, UserStatus
from ..services.user_service import UserService
from ..utils.postgres import SessionLocal
from ..utils.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        user_id = UUID(decode_access_token(credentials.credentials))
    except (InvalidTokenError, ValueError):
        raise unauthorized

    user = UserService(session).get_by_id(user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise unauthorized

    return user
