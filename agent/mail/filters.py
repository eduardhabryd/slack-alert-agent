from dataclasses import dataclass
from datetime import datetime
from agent.mail.client import EmailMessage
from agent.config.schema import MeetConfig
import logging

logger = logging.getLogger(__name__)

@dataclass
class MeetNotification:
    """Structured representation of a Google Meet/Calendar notification."""
    email_id: str
    title: str
    received_at: datetime
    status: str  # 'invitation', 'updated', 'cancelled', etc.

class MeetFilter:
    def __init__(self, config: 'MeetConfig'): # Use string forward ref or import if needed, but safe here
        self.config = config

    def filter_and_parse(self, emails: list[EmailMessage]) -> list[MeetNotification]:
        """
        Filter emails to keep only relevant Meet notifications.
        """
        notifications = []
        
        for email in emails:
            # Check sender (optional)
            if self.config.sender and self.config.sender not in email.sender:
                continue

            # Check keywords 
            subject_lower = email.subject.lower()
            if self.config.subject_keywords:
                matched = False
                for k in self.config.subject_keywords:
                    if k.lower() in subject_lower:
                        matched = True
                        break
                if not matched:
                    continue

            # Check body for specific Google Calendar footer or Meet links
            # User requested "Invitation from Google Calendar", but we also found "Join with Google Meet" in the debug logs.
            # We allow either to be robust.
            valid_body_phrases = ["Invitation from Google Calendar", "Join with Google Meet", "meet.google.com"]
            if not any(phrase in email.body for phrase in valid_body_phrases):
                 continue

            # Determine status
            status = "invitation"
            if "cancel" in subject_lower:
                status = "cancelled"
            elif "update" in subject_lower:
                status = "updated"
            
            # Create notification object
            notification = MeetNotification(
                email_id=email.id,
                title=email.subject,
                received_at=email.timestamp,
                status=status
            )
            notifications.append(notification)
            logger.info(f"Identified Meet notification: {notification.title}")

        return notifications
