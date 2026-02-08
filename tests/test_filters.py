import unittest
from dataclasses import dataclass
from datetime import datetime
from agent.mail.client import EmailMessage
from agent.mail.filters import MeetFilter
from agent.config.schema import MeetConfig

class TestMeetFilter(unittest.TestCase):
    def setUp(self):
        self.config = MeetConfig(
            sender="calendar-notification@google.com",
            subject_keywords=["invitation", "canceled"]
        )
        self.filter = MeetFilter(self.config)

    def test_filter_matching(self):
        emails = [
            EmailMessage(
                id="1",
                sender="calendar-notification@google.com",
                subject="Invitation: Standup @ Mon Feb 8",
                snippet="...",
                body="... Invitation from Google Calendar ...",
                timestamp=datetime.now(),
                is_read=False
            ),
            EmailMessage(
                id="2",
                sender="notification@slack.com",
                subject="Slack msg",
                snippet="...",
                body="...",
                timestamp=datetime.now(),
                is_read=False
            ),
            EmailMessage(
                id="3",
                sender="calendar-notification@google.com",
                subject="Canceled: Meeting",
                snippet="...",
                body="... Invitation from Google Calendar ...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        
        results = self.filter.filter_and_parse(emails)
        
        # Should match #1 (invitation) and #3 (canceled)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].email_id, "1")
        self.assertEqual(results[0].status, "invitation")
        self.assertEqual(results[1].email_id, "3")
        self.assertEqual(results[1].status, "cancelled")

    def test_filter_no_keywords(self):
        # Config without keywords (should match sender only if keywords logic allowed it, 
        # but our filter requires keywords if config has them, here we test empty keywords matches all from sender?)
        # Current logic: if self.config.subject_keywords is list, it enforces them.
        # If we pass empty list, it skips keyword check.
        config = MeetConfig(sender="calendar-notification@google.com", subject_keywords=[])
        test_filter = MeetFilter(config)
        
        emails = [
            EmailMessage(
                id="1",
                sender="calendar-notification@google.com",
                subject="Random email",
                snippet="...",
                body="... Invitation from Google Calendar ...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        results = test_filter.filter_and_parse(emails)
        self.assertEqual(len(results), 1)

    def test_filter_any_sender(self):
        # Config with sender=None (should match any sender based on keywords)
        config = MeetConfig(sender=None, subject_keywords=["invitation"])
        test_filter = MeetFilter(config)
        
        emails = [
            EmailMessage(
                id="1",
                sender="person@example.com",
                subject="Invitation: Meeting",
                snippet="...",
                body="... Invitation from Google Calendar ...",
                timestamp=datetime.now(),
                is_read=False
            ),
            EmailMessage(
                id="2",
                sender="other@example.com",
                subject="Just hi",
                snippet="...",
                body="...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        results = test_filter.filter_and_parse(emails)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].email_id, "1")

    def test_filter_missing_body_text(self):
        # Email matching keywords but missing footer text should be ignored
        config = MeetConfig(sender=None, subject_keywords=["invitation"])
        test_filter = MeetFilter(config)
        
        emails = [
            EmailMessage(
                id="1",
                sender="spammer@example.com",
                subject="Invitation: Fake Meeting",
                snippet="...",
                body="This is a fake invite without the google footer.",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        results = test_filter.filter_and_parse(emails)
        self.assertEqual(len(results), 0)

    def test_filter_join_with_google_meet(self):
        # Email with "Join with Google Meet" but without "Invitation from Google Calendar" should pass
        config = MeetConfig(sender=None, subject_keywords=["invitation"])
        test_filter = MeetFilter(config)
        
        emails = [
            EmailMessage(
                id="1",
                sender="colleague@example.com",
                subject="Invitation: Works",
                snippet="...",
                body="... Join with Google Meet ... link ...",
                timestamp=datetime.now(),
                is_read=False
            )
        ]
        results = test_filter.filter_and_parse(emails)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].email_id, "1")

if __name__ == '__main__':
    unittest.main()
