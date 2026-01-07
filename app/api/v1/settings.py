from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ...database import get_db
from ...models.settings import SystemSettings
from ...models.user import User, UserRole
from ..deps import get_current_user
from ...config import settings
from ...services.email import email_service
from pydantic import BaseModel, EmailStr

router = APIRouter()

# ============== System Settings Models ==============
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

# ============== Email Settings Models ==============
class EmailSettingsUpdate(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from_email: EmailStr
    smtp_from_name: str

class EmailSettingsResponse(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from_email: str
    smtp_from_name: str
    smtp_configured: bool

class TestEmailRequest(BaseModel):
    test_email: EmailStr

# ============== System Settings Endpoints ==============
@router.get("/", response_model=List[SettingResponse])
async def get_settings(
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
async def get_setting(
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
async def update_setting(
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
    db.refresh(setting)
    
    return {"message": "Setting updated successfully", "key": key, "value": setting_data.value}

# ============== Email Settings Endpoints ==============
@router.get("/email", response_model=EmailSettingsResponse)
async def get_email_settings(
    current_user: User = Depends(get_current_user)
):
    """Get email settings (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "smtp_host": settings.SMTP_HOST or "",
        "smtp_port": settings.SMTP_PORT or 587,
        "smtp_user": settings.SMTP_USER or "",
        "smtp_from_email": settings.SMTP_FROM_EMAIL or "",
        "smtp_from_name": settings.SMTP_FROM_NAME or "",
        "smtp_configured": bool(settings.SMTP_USER and settings.SMTP_PASSWORD)
    }

@router.post("/email/test")
async def test_email_settings(
    request_data: TestEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send test email (Admin only)"""
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if email is configured
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        raise HTTPException(
            status_code=400, 
            detail="Email not configured. Please configure SMTP settings first."
        )
    
    html_content = """
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Test Email</h2>
        <p>This is a test email from Phase-1 Employee Management System.</p>
        <p>If you received this, your email configuration is working correctly! ✅</p>
        <hr style="border: 1px solid #eee; margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
            This is an automated test email. Please do not reply.
        </p>
    </div>
    """
    
    text_content = """
    Test Email
    
    This is a test email from Phase-1 Employee Management System.
    If you received this, your email configuration is working correctly!
    
    This is an automated test email. Please do not reply.
    """
    
    success = await email_service.send_email(
        to_email=request_data.test_email,
        subject="Test Email - Phase-1 System",
        html_content=html_content,
        text_content=text_content
    )
    
    if success:
        return {
            "message": "Test email sent successfully",
            "recipient": request_data.test_email
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail="Failed to send test email. Please check your SMTP configuration."
        )