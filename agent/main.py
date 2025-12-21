import logging
import sys
from agent.config.loader import load_config
from agent.time.window import TimeWindow
from agent.email.gmail_client import GmailClient
from agent.email.filters import SlackFilter
from agent.notifier.telegram_call import TelegramCallNotifier
from agent.state.store import StateStore
from agent.logging.setup import setup_logging

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
        notifier = TelegramCallNotifier(config.telegram.call)
        state = StateStore()

        # 5. Fetch and Filter
        # Fetching unread emails from the configured sender
        emails = gmail.get_unread_emails(sender_filter=config.email.slack_sender)
        slack_notifications = slack_filter.filter_and_parse(emails)

        if not slack_notifications:
            logger.info("No Slack notifications found.")
            sys.exit(0)

        # 6. Deduplication
        new_alerts = []
        for notif in slack_notifications:
            if not state.is_processed(notif.email_id):
                 new_alerts.append(notif)
            else:
                logger.debug(f"Skipping processed email {notif.email_id}")

        if not new_alerts:
            logger.info("No new unique notifications.")
            sys.exit(0)

        logger.info(f"Found {len(new_alerts)} new notifications.")
        
        # 7. Notify
        message = config.telegram.call.message
        if notifier.notify(message):
            logger.info("Notification sent successfully.")
            # Update state logic: Mark as processed
            state.add_processed([n.email_id for n in new_alerts])
            
            # Optional: Mark emails as read in Gmail functionality
            # gmail.mark_as_read([n.email_id for n in new_alerts])
        else:
            logger.error("Failed to send notification. State not updated.")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
