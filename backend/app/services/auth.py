from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import uuid
from datetime import datetime
from ..core.security import verify_password, get_password_hash, create_access_token, verify_token
from ..models.user import User, UserCreate, UserInDB, UserLogin

# Simple in-memory user store for MVP (replace with database in production)
users_db: dict[str, UserInDB] = {}

security = HTTPBearer()


class AuthService:
    def __init__(self):
        self.users_db = users_db

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username."""
        for user in self.users_db.values():
            if user.username == username:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        for user in self.users_db.values():
            if user.email == email:
                return user
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username and password."""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user."""
        # Check if user already exists
        if self.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = get_password_hash(user_data.password)
        now = datetime.utcnow()
        
        db_user = UserInDB(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            is_active=user_data.is_active,
            hashed_password=hashed_password,
            created_at=now,
            updated_at=now
        )
        
        self.users_db[user_id] = db_user
        return db_user

    def login_user(self, login_data: UserLogin) -> dict:
        """Login user and return access token."""
        user = self.authenticate_user(login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}


# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")
    
    auth_service = AuthService()
    user = auth_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )
