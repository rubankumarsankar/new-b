from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+pymysql://root:ayati@localhost/my_database"
    
    # JWT
    SECRET_KEY: str = "tkzlyTWanFz91gorvbQG-iC1XqEC6H3o3atFJCzkbpE"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # App
    PROJECT_NAME: str = "Phase-1 Employee Management System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Office Hours
    OFFICE_START_TIME: str = "09:30"
    OFFICE_END_TIME: str = "18:30"
    GRACE_PERIOD_MINUTES: int = 15
    
    # Email Configuration
    SMTP_HOST: str = "mail.ayatiworks.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = "emailsmtp@ayatiworks.com"  # Your email
    SMTP_PASSWORD: str = "hYd@W,$nwNjC"  # Your email password or app password
    SMTP_FROM_EMAIL: str = "emailsmtp@ayatiworks.com"  # Sender email
    SMTP_FROM_NAME: str = " HR Team"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    
    # Teams Integration
    TEAMS_WEBHOOK_URL: Optional[str] = None
    
    # Outlook Integration
    OUTLOOK_CLIENT_ID: Optional[str] = None
    OUTLOOK_CLIENT_SECRET: Optional[str] = None
    OUTLOOK_TENANT_ID: Optional[str] = None
    
    # CORS - Fixed type annotation
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()