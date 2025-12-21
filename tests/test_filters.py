import unittest
from datetime import datetime
from agent.email.client import EmailMessage
from agent.email.filters import SlackFilter
from agent.config.schema import EmailConfig

class TestSlackFilter(unittest.TestCase):
    def setUp(self):
        self.config = EmailConfig(
            provider="gmail",
            slack_sender="notification@slack.com",
            subject_keywords=["urgent"]
        )
        self.filter = SlackFilter(self.config)

    def test_filter_matching(self):
        emails = [
            EmailMessage(
                id="1",
                sender="notification@slack.com",
                subject="URGENT: Server down",
                snippet="...",
                timestamp=datetime.now(),
                is_read=False
            ),
            EmailMessage(
                id="2",
                sender="notification@slack.com",
                subject="Just a regular message",
                snippet="...",
                timestamp=datetime.now(),
                is_read=False
            ),
            EmailMessage(
                id="3",
                sender="spam@example.com",
                subject="URGENT: Buy now",
                snippet="...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        
        results = self.filter.filter_and_parse(emails)
        
        # Should match #1 only (sender match + keyword match)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].email_id, "1")
        self.assertEqual(results[0].title, "URGENT: Server down")

    def test_filter_no_keywords(self):
        # Config without keywords
        config = EmailConfig(slack_sender="notification@slack.com", subject_keywords=[])
        test_filter = SlackFilter(config)
        
        emails = [
            EmailMessage(
                id="1",
                sender="notification@slack.com",
                subject="Hi",
                snippet="...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        results = test_filter.filter_and_parse(emails)
        self.assertEqual(len(results), 1)

if __name__ == '__main__':
    unittest.main()
