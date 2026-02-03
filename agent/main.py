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
from agent.slack.client import SlackSessionClient

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
        notifier_manager = NotificationManager(config.notifications)
        state = StateStore() # State might not be needed for API mode if we just want current status, but useful for dedup logic if we want to add it later.
                             # For now, API mode alerts on count > 0.
        
        if config.mode == "api":
            logger.info("Running in API (Session Token) mode.")
            if not config.slack or not config.slack.token or not config.slack.cookie:
                logger.error("Slack session configuration missing (token, cookie, or workspace_url).")
                sys.exit(1)
            
            slack_client = SlackSessionClient(
                token=config.slack.token, 
                cookie=config.slack.cookie, 
                workspace_url=config.slack.workspace_url
            )
            
            try:
                result = slack_client.get_unread_count()
                unread_count = result['unread_count']
                logger.info(f"Unread Slack messages: {unread_count}")
                
                if unread_count > 0:
                     # Alert!
                     message = f"You have {unread_count} unread Slack messages."
                     if notifier_manager.notify(message):
                         logger.info("Notification sent.")
                     else:
                         logger.error("Failed to notify.")
            
            except PermissionError:
                 logger.critical("Slack session token expired or invalid!")
                 # Send critical alert via Pushover specifically
                 # We construct a specific message for this
                 notifier_manager.notify("CRITICAL: Slack session token expired. Please update credentials.")
                 sys.exit(1)
                 
        else: # Default or 'email' mode
            logger.info("Running in Email Parsing mode.")
            # Connect to Email
            gmail = GmailClient()
            gmail.connect()
            
            # Helper objects
            slack_filter = SlackFilter(config.email)

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
                pass
            else:
                logger.error("Failed to send notification via any configured channel.")
                sys.exit(1)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        # Attempt to send a critical alert via Pushover if possible
        try:
            # We need to initialize notifier just for this if not already done, 
            # but usually it dies before loop. If it dies inside loop, notifier_manager exists.
            # Safety check:
            if 'notifier_manager' in locals():
                notifier_manager.notify(f"CRITICAL AGENT ERROR: {e}")
            else:
                # Try to load minimal config to send alert? 
                # Or just rely on logs. For now, let's try to reuse if available.
                pass
        except:
            pass
            
        sys.exit(1)

if __name__ == "__main__":
    main()
