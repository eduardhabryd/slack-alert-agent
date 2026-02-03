import logging
import requests
import time
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class SlackSessionClient:
    """
    Client to interact with Slack's internal API using session token and cookie.
    """
    def __init__(self, token: str, cookie: str, workspace_url: str):
        self.token = token
        self.cookie = cookie
        self.workspace_url = workspace_url.rstrip('/')
        
        if "app.slack.com" in self.workspace_url:
            logger.warning(f"Your workspace_url '{self.workspace_url}' looks like the web interface.")
            logger.warning("You should likely use your workspace domain, e.g., 'https://your-company.slack.com'.")
            
        self.headers = {
            "Cookie": f"d={self.cookie}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_unread_count(self) -> Dict[str, Any]:
        """
        Queries client.counts to get the unread count.
        Returns a dict with 'unread_count_display' and status.
        Raises exception if auth fails.
        """
        url = f"{self.workspace_url}/api/client.counts"
        
        params = {
            "token": self.token,
            "include_archived_channels_on_client_counts": 1
        }

        try:
            # Note: client.counts usually expects form-data for 'token', not query params.
            response = requests.post(url, data=params, headers=self.headers, timeout=10)
            
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError:
                logger.error(f"Failed to decode JSON. Status: {response.status_code}")
                snippet = response.text[:500]
                logger.error(f"Response text: {snippet}") 
                
                if "<!DOCTYPE html>" in snippet or "<html" in snippet:
                    raise Exception(
                        f"Slack returned HTML instead of JSON. "
                        f"Please check your 'workspace_url'. It should be 'https://your-team.slack.com', "
                        f"not 'https://app.slack.com/client/...'"
                    )
                    
                raise Exception(f"Invalid response from Slack (Status {response.status_code})")

            if not response.ok: # Check for HTTP errors after attempting to parse JSON (or use raise_for_status before)
                 response.raise_for_status()

            if not data.get("ok"):
                error = data.get("error")
                logger.error(f"Slack API error: {error}")
                if error == 'invalid_auth':
                    raise PermissionError("Slack session token/cookie is invalid or expired.")
                raise Exception(f"Slack API returned error: {error}")

            # 'unread_count_display' might be missing in newer API versions.
            # Use 'channel_badges' or sum up unreads manually.
            unread_count = data.get("unread_count_display")
            
            if unread_count is None:
                # Fallback: Sum up badges which represent "Red Dot" notifications (Mentions)
                badges = data.get("channel_badges")
                
                if badges is None:
                    # If both unread_count_display AND channel_badges are missing, the API has changed.
                    # We must raise an error to alert the user via the global exception handler.
                    raise Exception("Slack API response missing 'unread_count_display' and 'channel_badges'. API structure may have changed.")
                
                # We interpret the user's request for "only channel mentions" as:
                # 1. Channel Mentions (badges['channels']) - This is the red badge count.
                # 2. DMs (badges['dms']) - Direct messages from people.
                # 3. Thread Mentions (badges['thread_mentions']) - Replies effectively mentioning you.
                # We EXCLUDE 'app_dms' (Bots) and 'thread_unreads' (unless mentioned).
                
                unread_count = (
                    badges.get("channels", 0) + 
                    badges.get("dms", 0) + 
                    badges.get("thread_mentions", 0)
                )

            return {
                "unread_count": unread_count,
                "raw_data": data
            }

        except requests.RequestException as e:
            logger.error(f"Failed to connect to Slack: {e}")
            raise

    def validate_session(self) -> bool:
        """
        Checks if the current session credentials are valid.
        """
        try:
            self.get_unread_count()
            return True
        except PermissionError:
            return False
        except Exception:
            # Other errors (network, etc) don't necessarily mean invalid session
            # But for simplicity, we might just log it.
            return False


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    client = SlackSessionClient(
        token=os.getenv("SLACK_TOKEN"),
        cookie=os.getenv("SLACK_COOKIE"),
        workspace_url=os.getenv("SLACK_WORKSPACE_URL")
    )
    print(client.get_unread_count()['raw_data']['channel_badges'])