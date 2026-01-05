from datetime import timedelta, datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...database import get_db
from ...models.user import User, UserRole
from ...core.security import verify_password, create_access_token, get_password_hash
from ...config import settings
from pydantic import BaseModel, EmailStr
import secrets

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.EMPLOYEE

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_code: str
    new_password: str

# Store reset codes in memory (use Redis in production)
reset_codes = {}

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Login endpoint - returns JWT token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "is_active": user.is_active
        }
    }

@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Generate password reset code"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset code will be sent"}
    
    # Generate 6-digit code
    reset_code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Store with expiration (10 minutes)
    reset_codes[request.email] = {
        "code": reset_code,
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    # TODO: Send email with reset code
    # send_reset_code_email(user.email, reset_code)
    
    print(f"Password reset code for {request.email}: {reset_code}")  # For testing
    
    return {"message": "If the email exists, a reset code will be sent"}

@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using reset code"""
    # Check if reset code exists
    if request.email not in reset_codes:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code")
    
    stored_data = reset_codes[request.email]
    
    # Check if code matches
    if stored_data["code"] != request.reset_code:
        raise HTTPException(status_code=400, detail="Invalid reset code")
    
    # Check if code is expired
    if datetime.utcnow() > stored_data["expires_at"]:
        del reset_codes[request.email]
        raise HTTPException(status_code=400, detail="Reset code has expired")
    
    # Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    # Remove used reset code
    del reset_codes[request.email]
    
    return {"message": "Password reset successfully"}

@router.post("/register", response_model=UserResponse)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register new user"""
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user