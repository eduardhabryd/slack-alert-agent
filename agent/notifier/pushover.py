import requests
import logging
from typing import Optional
from agent.notifier.base import Notifier
from agent.config.schema import PushoverConfig

logger = logging.getLogger(__name__)

class PushoverNotifier(Notifier):
    def __init__(self, config: PushoverConfig):
        self.config = config
        self.url = "https://api.pushover.net/1/messages.json"

    def notify(self, message: str) -> bool:
        if not self.config.enabled:
            logger.info("Pushover disabled by config.")
            return True # Not an failure, just skipped.

        if not self.config.user_key or not self.config.api_token:
             logger.error("Pushover credentials (user_key or api_token) missing.")
             return False

        payload = {
            "token": self.config.api_token,
            "user": self.config.user_key,
            "message": message,
            "priority": self.config.priority,
            "retry": 30, # Required for priority 2 (emergency)
            "expire": 3600, # Required for priority 2 (emergency)
            "sound": "siren" # Optional, can be configurable later
        }

        try:
            logger.info(f"Sending Pushover notification (Priority: {self.config.priority})...")
            response = requests.post(self.url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Pushover notification sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Pushover. Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            logger.exception(f"Error making request to Pushover: {e}")
            return False
