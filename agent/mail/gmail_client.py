import os
import logging
import base64
from datetime import datetime
from typing import List, Optional
from email import message_from_bytes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from agent.mail.client import EmailClient, EmailMessage

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailClient(EmailClient):
    def __init__(self):
        self.service = None

    def connect(self):
        """
        Authenticate using credentials from environment variables.
        Requires:
        - GMAIL_CLIENT_ID
        - GMAIL_CLIENT_SECRET
        - GMAIL_REFRESH_TOKEN
        """
        creds = None
        
        # Load tokens from env
        client_id = os.getenv('GMAIL_CLIENT_ID')
        client_secret = os.getenv('GMAIL_CLIENT_SECRET')
        refresh_token = os.getenv('GMAIL_REFRESH_TOKEN')

        if client_id and client_secret and refresh_token:
            logger.info("Using credentials from environment.")
            creds = Credentials(
                None, # No access token initially
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )
        else:
            # Fallback for local dev - try to load token.json
            if os.path.exists('token.json'):
                logger.info("Loading credentials from token.json")
                try:
                    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                except Exception as e:
                    logger.error(f"Failed to load token.json: {e}")
            else:
                 # Local interactive flow (only if strictly needed, usually avoiding in agent)
                 logger.warning("No credentials found in env or token.json.")

        if creds and not creds.valid and creds.refresh_token:
            logger.info("Credentials invalid or expired. Refreshing...")
            try:
                creds.refresh(Request())
                logger.info("Refresh completed.")
            except Exception as e:
                logger.error(f"Refresh failed: {e}")
                # We don't raise here, we let the check below handle it (or maybe we should raise)

        if not creds or not creds.valid:
            raise Exception("Could not authenticate with Gmail. Check credentials.")

        self.service = build('gmail', 'v1', credentials=creds)
        logger.info("Successfully connected to Gmail API.")

    def get_emails(self, sender_filter: Optional[str] = None, only_unread: bool = False) -> List[EmailMessage]:
        if not self.service:
            raise Exception("Client not connected. Call connect() first.")

        query = 'label:INBOX'
        if only_unread:
            query += ' is:unread'
        if sender_filter:
            query += f' from:{sender_filter}'

        logger.info(f"Querying Gmail with: {query}")
        
        results = self.service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        email_objects = []
        if not messages:
            logger.info("No messages found.")
            return []

        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '(Unknown)')
            
            # Internal date is ms timestamp
            internal_date = int(msg_data.get('internalDate', 0))
            timestamp = datetime.fromtimestamp(internal_date / 1000.0)
            
            # Extract body
            body = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            body += base64.urlsafe_b64decode(data).decode()
            elif 'body' in payload:
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode()
            
            # Fallback to snippet if body is empty
            if not body:
                body = msg_data.get('snippet', '')

            email_objects.append(EmailMessage(
                id=msg['id'],
                sender=sender,
                subject=subject,
                snippet=msg_data.get('snippet', ''),
                body=body,
                timestamp=timestamp,
                is_read=False
            ))

        return email_objects

    def mark_as_read(self, email_ids: List[str]):
        if not self.service:
             raise Exception("Client not connected.")

        if not email_ids:
            return

        batch = {
            'ids': email_ids,
            'removeLabelIds': ['UNREAD']
        }
        
        self.service.users().messages().batchModify(userId='me', body=batch).execute()
        logger.info(f"Marked {len(email_ids)} emails as read.")
