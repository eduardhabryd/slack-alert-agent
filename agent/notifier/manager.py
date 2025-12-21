import logging
from typing import Dict
from agent.notifier.base import Notifier
from agent.notifier.telegram_call import TelegramCallNotifier
from agent.notifier.pushover import PushoverNotifier
from agent.config.schema import NotificationConfig

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, config: NotificationConfig):
        self.config = config
        self.notifiers: Dict[str, Notifier] = {}
        
        # Initialize supported notifiers
        self.notifiers['telegram_call'] = TelegramCallNotifier(config.telegram.call)
        self.notifiers['pushover'] = PushoverNotifier(config.pushover)

    def notify(self, message: str) -> bool:
        """
        Executes the configured notification strategy.
        Returns True if at least one notification was successful (or the strategy was satisfied).
        """
        strategy = self.config.strategy
        ordered_notifiers = [n for n in strategy.order if n in self.notifiers]
        
        if not ordered_notifiers:
            logger.warning("No valid notifiers found in strategy order.")
            return False

        success = False
        
        logger.info(f"Starting notification strategy: Order={ordered_notifiers}, StopAfterSuccess={strategy.stop_after_success}")

        for name in ordered_notifiers:
            notifier = self.notifiers[name]
            logger.info(f"Attempting notification via {name}...")
            
            if notifier.notify(message):
                success = True
                logger.info(f"Notification via {name} succeeded.")
                
                if strategy.stop_after_success:
                    logger.info("Stop after success is enabled. Stopping strategy.")
                    return True
            else:
                logger.warning(f"Notification via {name} failed.")
        
        if not success:
            logger.error("All notification attempts failed.")
            
        return success
