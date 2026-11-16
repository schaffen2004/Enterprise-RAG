from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..model.user import User, UserStatus
from ..schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead
from ..services.user_service import DuplicateUserError, UserService
from ..utils.security import create_access_token
from .dependencies import get_current_user, get_db

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, session: Session = Depends(get_db)) -> User:
    try:
        return UserService(session).register(
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, session: Session = Depends(get_db)) -> TokenResponse:
    user = UserService(session).authenticate(
        username=payload.username, password=payload.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
