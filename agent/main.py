import logging
import sys
import os

# Add project root to sys.path to allow running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.config.loader import load_config
from agent.time.window import TimeWindow
from agent.mail.gmail_client import GmailClient
from agent.mail.filters import MeetFilter
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
        
        messages_to_notify = []
        
        # --- 4a. Slack API Check ---
        if config.slack and config.slack.token:
            logger.info("Checking Slack API...")
            try:
                slack_client = SlackSessionClient(
                    token=config.slack.token, 
                    cookie=config.slack.cookie, 
                    workspace_url=config.slack.workspace_url
                )
                
                result = slack_client.get_unread_count()
                unread_count = result['unread_count']
                logger.info(f"Unread Slack messages: {unread_count}")
                
                if unread_count > 0:
                     messages_to_notify.append(f"You have {unread_count} unread Slack messages.")
            except PermissionError:
                 logger.critical("Slack session token expired!")
                 messages_to_notify.append("CRITICAL: Slack session token expired.")
            except Exception as e:
                logger.error(f"Slack check failed: {e}")

        # --- 4b. Google Meet Check ---
        if config.meet and config.meet.enabled:
            logger.info("Checking Gmail for Meet invitations...")
            try:
                gmail = GmailClient()
                gmail.connect()
                
                meet_filter = MeetFilter(config.meet)
                
                # Fetching ALL emails from the configured sender (persistent alert mode)
                emails = gmail.get_emails(sender_filter=config.meet.sender, only_unread=False)
                meet_notifications = meet_filter.filter_and_parse(emails)

                if meet_notifications:
                    count = len(meet_notifications)
                    logger.info(f"Found {count} Meet notifications.")
                    # Create a summary message
                    titles = [n.title for n in meet_notifications[:3]] # First 3
                    msg = f"Found {count} Google Meet events: " + ", ".join(titles)
                    messages_to_notify.append(msg)
                else:
                    logger.info("No Meet notifications found.")
            except Exception as e:
                logger.error(f"Meet check failed: {e}")

        # --- 5. Notify ---
        if messages_to_notify:
            logger.info("Alerts triggered. Sending notifications...")
            full_message = "\n".join(messages_to_notify)
            
            # If we utilize the configured message from config, we might override it or append to it.
            # config.notifications.telegram.call.message is usually static. 
            # Let's try to use the dynamic message if the notifier supports it, 
            # but for safety (CallMeBot limitation might be length), we keep it short or combine.
            
            # Note: The original code used config.notifications.telegram.call.message. 
            # We should probably pass the specific message to the notifier if possible.
            # The NotificationManager.notify(message) signature accepts a string.
            
            if notifier_manager.notify(full_message):
                logger.info("Notifications sent successfully.")
            else:
                logger.error("Failed to notify.")
                sys.exit(1)
        else:
            logger.info("No alerts needed.")

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
