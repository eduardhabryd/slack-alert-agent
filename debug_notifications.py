import logging
import sys
import os
from dotenv import load_dotenv

# Force load .env
load_dotenv()

# Setup logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agent.config.loader import load_config
from agent.notifier.manager import NotificationManager

def test_notifications():
    print("Loading config...", flush=True)
    try:
        config = load_config()
    except Exception as e:
        print(f"Config load failed: {e}")
        return

    print("Config Loaded Debug:", flush=True)
    print(f"Telegram User: '{config.notifications.telegram.call.username}'", flush=True)
    print(f"Pushover User Key: '{config.notifications.pushover.user_key}'", flush=True)
    print(f"Pushover Token: '{config.notifications.pushover.api_token}'", flush=True)
    print(f"Strategy: {config.notifications.strategy.order}", flush=True)

    # FORCE override for testing
    config.notifications.strategy.order = ['pushover']
    print("Forced Strategy: ['pushover']", flush=True)

    manager = NotificationManager(config.notifications)
    
    print("\nAttempting to send TEST notification...", flush=True)
    result = manager.notify("TEST NOTIFICATION from Slack Alert Agent")
    
    print(f"\nFinal Result: {result}", flush=True)

if __name__ == "__main__":
    test_notifications()
