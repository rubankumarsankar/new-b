from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..database import Base

class NotificationType(str, enum.Enum):
    TASK_ASSIGNED = "task_assigned"
    TASK_OVERDUE = "task_overdue"
    ATTENDANCE_LATE = "attendance_late"
    ATTENDANCE_MISSED = "attendance_missed"
    BLOG_REVIEW = "blog_review"
    BLOG_PUBLISHED = "blog_published"
    GENERAL = "general"

class NotificationChannel(str, enum.Enum):
    SYSTEM = "system"
    TEAMS = "teams"
    OUTLOOK = "outlook"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    error_message = Column(Text)
    meta_data = Column(Text)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")