"""
Authentication endpoints - Login and Token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import get_db
from utils.auth import verify_password
from crud import get_user_by_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    userId: int
    name: str
    email: str
    phone: str
    role: str
    message: str

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password
    """
    # Get user by email
    user = get_user_by_email(db, credentials.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Get role from database (secure - cannot be manipulated)
    role = user.role.value if user.role else "user"
    
    return LoginResponse(
        userId=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        role=role,
        message="Login successful"
    )

