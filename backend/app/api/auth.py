from fastapi import APIRouter, HTTPException, status, Depends
from ..models.user import UserCreate, UserLogin, User, Token
from ..services.auth import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate):
    """Register a new user."""
    try:
        user = auth_service.create_user(user_data)
        return {
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user and return access token."""
    try:
        token_data = auth_service.login_user(login_data)
        return Token(**token_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error logging in: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should remove token)."""
    return {"message": "Logged out successfully"}
