from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def register(self, request: UserCreate) -> User:
        existing_user = self.user_repository.get_by_email(request.email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            role=request.role,
            is_active=True,
        )

        self.user_repository.create(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.user_repository.get_by_email(request.email)

        if user is None or not verify_password(
            request.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        access_token = create_access_token(str(user.id))

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )