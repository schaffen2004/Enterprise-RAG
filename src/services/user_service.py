from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..model.user import User
from ..utils.security import hash_password, verify_password


class DuplicateUserError(Exception):
    """Raised when a username or email already exists."""


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def register(self, username: str, email: str, password: str) -> User:
        if self.get_by_username(username) is not None:
            raise DuplicateUserError("Username already taken")
        if self.get_by_email(email) is not None:
            raise DuplicateUserError("Email already registered")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
        )
        try:
            self.session.add(user)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateUserError("Username or email already exists") from exc
        self.session.refresh(user)
        return user

    def authenticate(self, username: str, password: str) -> User | None:
        user = self.get_by_username(username)
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user

    def delete(self, user_id: UUID) -> bool:
        user = self.session.get(User, user_id)
        if user is None:
            return False
        self.session.delete(user)
        self.session.commit()
        return True
