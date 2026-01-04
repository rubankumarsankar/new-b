from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..core.security import decode_access_token
from ..models.user import User, UserRole
from ..core.permissions import has_permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """Get current authenticated user"""
    print(f"🔍 Received token: {token[:20]}..." if token else "❌ No token received")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        print("❌ Token is empty")
        raise credentials_exception
    
    payload = decode_access_token(token)
    if payload is None:
        print("❌ Token decode failed")
        raise credentials_exception
    
    # FIX: Convert string back to integer
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        print("❌ No user_id in token payload")
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)  # ← Convert string to int
    except ValueError:
        print(f"❌ Invalid user_id format: {user_id_str}")
        raise credentials_exception
    
    print(f"✅ Token valid, user_id: {user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"❌ User {user_id} not found in database")
        raise credentials_exception
    
    if not user.is_active:
        print(f"❌ User {user_id} is inactive")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    print(f"✅ User authenticated: {user.username}")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_roles: list):
    """Dependency to require specific roles"""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def require_permission(permission: str):
    """Dependency to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission}"
            )
        return current_user
    return permission_checker