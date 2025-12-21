import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from agent.config.schema import TimeWindowConfig
from agent.time.window import TimeWindow
import pytz

class TestTimeWindow(unittest.TestCase):
    def test_disabled(self):
        config = TimeWindowConfig(enabled=False)
        self.assertTrue(TimeWindow.is_working_hours(config))

    @patch('agent.time.window.datetime')
    def test_within_window(self, mock_datetime):
        # Mocking time: Wed 12:00
        tz = pytz.timezone("UTC")
        mock_now = datetime(2023, 10, 25, 12, 0, 0, tzinfo=tz) # Wed
        mock_datetime.now.return_value = mock_now
        
        config = TimeWindowConfig(
            enabled=True,
            timezone="UTC",
            start="09:00",
            end="17:00",
            days=[0, 1, 2, 3, 4] # Mon-Fri
        )
        self.assertTrue(TimeWindow.is_working_hours(config))

    @patch('agent.time.window.datetime')
    def test_outside_hours(self, mock_datetime):
        # Mocking time: Wed 18:00
        tz = pytz.timezone("UTC")
        mock_now = datetime(2023, 10, 25, 18, 0, 0, tzinfo=tz)
        mock_datetime.now.return_value = mock_now
        
        config = TimeWindowConfig(
            enabled=True,
            timezone="UTC",
            start="09:00",
            end="17:00",
            days=[0, 1, 2, 3, 4]
        )
        self.assertFalse(TimeWindow.is_working_hours(config))

    @patch('agent.time.window.datetime')
    def test_weekend(self, mock_datetime):
        # Mocking time: Sat 12:00
        tz = pytz.timezone("UTC")
        mock_now = datetime(2023, 10, 28, 12, 0, 0, tzinfo=tz) # Sat
        mock_datetime.now.return_value = mock_now
        
        config = TimeWindowConfig(days=[0, 1, 2, 3, 4])
        self.assertFalse(TimeWindow.is_working_hours(config))

if __name__ == '__main__':
    unittest.main()
