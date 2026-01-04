from typing import Dict, Any
import httpx
from ..config import settings
from ..models.notification import Notification, NotificationType, NotificationChannel
from sqlalchemy.orm import Session

async def send_teams_notification(title: str, message: str) -> bool:
    """Send notification to Microsoft Teams"""
    if not settings.TEAMS_WEBHOOK_URL:
        return False
    
    try:
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "activitySubtitle": message,
                "markdown": True
            }]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(settings.TEAMS_WEBHOOK_URL, json=payload)
            return response.status_code == 200
    except Exception as e:
        print(f"Teams notification error: {e}")
        return False

async def send_outlook_email(to_email: str, subject: str, body: str) -> bool:
    """Send email via Outlook API"""
    # Implementation depends on your Outlook setup
    # This is a placeholder
    return True

def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    channel: NotificationChannel,
    title: str,
    message: str
) -> Notification:
    """Create a notification in database"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        channel=channel,
        title=title,
        message=message
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification