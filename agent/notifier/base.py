from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def notify(self, message: str) -> bool:
        """
        Send a notification.
        Returns True if successful, False otherwise.
        """
        pass
