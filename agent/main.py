import logging
import sys
import os

# Add project root to sys.path to allow running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.config.loader import load_config
from agent.time.window import TimeWindow
from agent.mail.gmail_client import GmailClient
from agent.mail.filters import SlackFilter
from agent.notifier.manager import NotificationManager
from agent.state.store import StateStore
from agent.logs.setup import setup_logging

logger = logging.getLogger(__name__)

def main():
    # 1. Load Config
    try:
        config = load_config()
    except Exception as e:
        # Fallback logging if config load fails
        logging.basicConfig(level=logging.INFO)
        logging.critical(f"Failed to load config: {e}")
        sys.exit(1)

    # 2. Setup Logging
    setup_logging(config.logging)
    logger.info("Agent starting...")

    # 3. Check Time Window
    if not TimeWindow.is_working_hours(config.working_hours):
        logger.info("Outside working hours. Exiting.")
        sys.exit(0)

    # 4. Initialize Components
    try:
        # Connect to Email
        gmail = GmailClient()
        gmail.connect()
        
        # Helper objects
        slack_filter = SlackFilter(config.email)
        notifier_manager = NotificationManager(config.notifications)
        state = StateStore()

        # 5. Fetch and Filter
        # Fetching ALL emails from the configured sender (persistent alert mode)
        logger.info("Scanning for Slack notifications in Inbox (Persistent Mode)...")
        emails = gmail.get_emails(sender_filter=config.email.slack_sender, only_unread=False)
        slack_notifications = slack_filter.filter_and_parse(emails)

        if not slack_notifications:
            logger.info("No Slack notifications found in Inbox.")
            sys.exit(0)

        # 6. Persistent Alerting Logic
        # We alert if ANY matching email is found, regardless of state history.
        # This fulfills: "only stop notifications if email from slack is deleted"
        new_alerts = slack_notifications
        logger.info(f"Found {len(new_alerts)} active Slack notifications. Triggering alert.")
        
        # 7. Notify
        message = config.notifications.telegram.call.message
        
        if notifier_manager.notify(message):
            logger.info("Notification strategy completed successfully.")
            # In persistent mode, we don't need to update state because we want to alert again next time
            # if the email is still there.
            pass
        else:
            logger.error("Failed to send notification via any configured channel.")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
