import requests
import urllib.parse
import logging
import os
from agent.notifier.base import Notifier
from agent.config.schema import CallMeBotConfig

logger = logging.getLogger(__name__)

class TelegramCallNotifier(Notifier):
    def __init__(self, config: CallMeBotConfig):
        self.config = config
        self.api_key = os.getenv("TELEGRAM_CALLMEBOT_API_KEY") 
        # Note: CallMeBot usually uses username as key or a separate key. 
        # For the standard CallMeBot Telegram, it's user + text.
        # But commonly there's no API "key" in the strict sense for the free tier, 
        # just the username is authorized. However, if using the "Premium" or other variants, keys might exist.
        # Standard free CallMeBot:
        # GET http://api.callmebot.com/start.php?user=@user&text=msg&lang=en...
        pass

    def notify(self, message: str) -> bool:
        if not self.config.enabled:
            logger.info("Telegram call disabled by config.")
            return True

        username = self.config.username
        if not username:
             logger.error("Telegram username not configured. Cannot make call.")
             return False

        # Encode message
        encoded_msg = urllib.parse.quote(message)
        
        # Construct URL
        # Using the standard endpoint for Telegram CallMeBot
        url = f"http://api.callmebot.com/start.php?user={username}&text={encoded_msg}&lang=en-US-Standard-B&rpt=2"

        try:
            logger.info(f"Initiating call to {username}...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info("Call initiated successfully.")
                return True
            else:
                logger.error(f"Failed to initiate call. Status: {response.status_code}, Body: {response.text}")
                return False
        except Exception as e:
            logger.exception(f"Error making request to CallMeBot: {e}")
            return False
