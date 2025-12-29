from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmailMessage:
    """Generic email message representation."""
    id: str
    sender: str
    subject: str
    snippet: str
    timestamp: datetime
    is_read: bool

class EmailClient(ABC):
    """Abstract base class for email providers."""
    
    @abstractmethod
    def connect(self):
        """Authenticate and connect to the service."""
        pass

    @abstractmethod
    def get_emails(self, sender_filter: Optional[str] = None, only_unread: bool = False) -> List[EmailMessage]:
        """
        Fetch emails, optionally filtered by sender and read status.
        Should return a list of generic EmailMessage objects.
        """
        pass

    @abstractmethod
    def mark_as_read(self, email_ids: List[str]):
        """Mark specific emails as read."""
        pass
