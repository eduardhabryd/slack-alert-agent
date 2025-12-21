from datetime import datetime
import pytz
from agent.config.schema import TimeWindowConfig
import logging

logger = logging.getLogger(__name__)

class TimeWindow:
    @staticmethod
    def is_working_hours(config: TimeWindowConfig) -> bool:
        """
        Check if the current time is within the allowed working hours and days.
        """
        if not config.enabled:
            logger.info("Time window check disabled. Allowing execution.")
            return True

        try:
            tz = pytz.timezone(config.timezone)
        except pytz.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {config.timezone}. Blocking execution for safety.")
            return False

        now = datetime.now(tz)
        
        # Check day of week (0=Monday, 6=Sunday)
        if now.weekday() not in config.days:
            logger.info(f"Today is {now.strftime('%A')} (day {now.weekday()}), not in allowed days {config.days}. Skipping.")
            return False

        # Parse start and end times
        try:
            start_h, start_m = map(int, config.start.split(":"))
            end_h, end_m = map(int, config.end.split(":"))
        except ValueError:
            logger.error(f"Invalid time format in config (Start: {config.start}, End: {config.end}). Expected HH:MM.")
            return False

        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if start_minutes <= current_minutes <= end_minutes:
            logger.info(f"Current time {now.strftime('%H:%M')} is within working hours ({config.start}-{config.end}).")
            return True
        else:
            logger.info(f"Current time {now.strftime('%H:%M')} is OUTSIDE working hours ({config.start}-{config.end}). Skipping.")
            return False
