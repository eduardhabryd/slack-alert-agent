from dataclasses import dataclass
from datetime import datetime
from agent.email.client import EmailMessage
from agent.config.schema import EmailConfig
import logging

logger = logging.getLogger(__name__)

@dataclass
class SlackNotification:
    """Structured representation of a Slack notification."""
    email_id: str
    title: str
    received_at: datetime

class SlackFilter:
    def __init__(self, config: EmailConfig):
        self.config = config

    def filter_and_parse(self, emails: list[EmailMessage]) -> list[SlackNotification]:
        """
        Filter emails to keep only relevant Slack notifications.
        Returns a list of SlackNotification objects.
        """
        slack_notifications = []
        
        for email in emails:
            # Check sender (should be granular if slack sends from multiple subdomains, usually notification@slack.com)
            if self.config.slack_sender and self.config.slack_sender not in email.sender:
                continue

            # Check keywords if configured
            if self.config.subject_keywords:
                if not any(k.lower() in email.subject.lower() for k in self.config.subject_keywords):
                    continue

            # Create notification object
            # We assume the subject contains the useful info "You have a new message from..."
            notification = SlackNotification(
                email_id=email.id,
                title=email.subject,
                received_at=email.timestamp
            )
            slack_notifications.append(notification)
            logger.info(f"Identified Slack notification: {notification.title}")

        return slack_notifications
