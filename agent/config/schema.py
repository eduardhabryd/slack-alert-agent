from typing import List, Optional
from pydantic import BaseModel, Field

class TimeWindowConfig(BaseModel):
    """Configuration for working hours enforcement."""
    enabled: bool = True
    timezone: str = "UTC"
    start: str = "09:00"
    end: str = "17:00"
    days: List[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4])  # 0=Mon, 6=Sun

class EmailConfig(BaseModel):
    """Configuration for email provider."""
    provider: str = "gmail"
    slack_sender: str = "notification@slack.com"
    subject_keywords: List[str] = Field(default_factory=list)

class CallMeBotConfig(BaseModel):
    """Configuration for CallMeBot notifications."""
    enabled: bool = True
    message: str = "Urgent Slack notification detected."
    username: Optional[str] = None  # Can be overridden by env var

class TelegramConfig(BaseModel):
    """Configuration for Telegram notifications."""
    call: CallMeBotConfig = Field(default_factory=CallMeBotConfig)

class PushoverConfig(BaseModel):
    """Configuration for Pushover notifications."""
    enabled: bool = False
    user_key: Optional[str] = None # Can be overridden by env var
    api_token: Optional[str] = None # Can be overridden by env var
    priority: int = 1 # 0=Normal, 1=High, 2=Emergency (Critical Alert)

class NotificationStrategyConfig(BaseModel):
    """Configuration for notification behavior."""
    # Order of notifiers to try: 'telegram_call', 'pushover'
    order: List[str] = Field(default_factory=lambda: ["telegram_call"])
    # If true, stops after the first successful notification
    stop_after_success: bool = True

class NotificationConfig(BaseModel):
    """Grouped notification settings."""
    strategy: NotificationStrategyConfig = Field(default_factory=NotificationStrategyConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    pushover: PushoverConfig = Field(default_factory=PushoverConfig)

class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = "INFO"

class AppConfig(BaseModel):
    """Root configuration model."""
    working_hours: TimeWindowConfig = Field(default_factory=TimeWindowConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
