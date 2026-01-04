from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import get_db
from ...models.settings import SystemSettings
from ...models.user import User, UserRole
from ..deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str]
    category: Optional[str]
    
    class Config:
        from_attributes = True

class SettingUpdate(BaseModel):
    value: str

@router.get("/", response_model=List[SettingResponse])
def get_settings(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all system settings (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(SystemSettings).filter(SystemSettings.is_active == True)
    
    if category:
        query = query.filter(SystemSettings.category == category)
    
    return query.all()

@router.get("/{key}", response_model=SettingResponse)
def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get setting by key"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    return setting

@router.put("/{key}")
def update_setting(
    key: str,
    setting_data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update setting"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    setting.value = setting_data.value
    db.commit()
    
    return {"message": "Setting updated successfully", "key": key, "value": setting_data.value}