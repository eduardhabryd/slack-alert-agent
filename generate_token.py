import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load env to get Client ID/Secret
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def generate_token():
    client_id = os.getenv('GMAIL_CLIENT_ID')
    client_secret = os.getenv('GMAIL_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Error: GMAIL_CLIENT_ID or GMAIL_CLIENT_SECRET not found in .env")
        return

    logger.info("Starting OAuth Flow...")
    logger.info("Client ID found: %s...", client_id[:10])

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        SCOPES
    )

    # run_local_server(open_browser=False) will print the URL to the console.
    # Users can copy this URL to an Incognito window to sign in with the correct account.
    logger.info("\n" + "="*60)
    logger.info("ACTION REQUIRED:")
    logger.info("1. Copy the URL below.")
    logger.info("2. Paste it into an INCOGNITO / PRIVATE browser window.")
    logger.info("3. Sign in with 'eduard.habryd@boosta.co'.")
    logger.info("4. If you see a 'site can't be reached' error after signing in, look at the URL bar.")
    logger.info("   It will allow the script to capture the code automatically if on localhost,")
    logger.info("   or you might need to copy the code if using console flow (though local server is usually automatic).")
    logger.info("="*60 + "\n")

    creds = flow.run_local_server(port=0, prompt='select_account', open_browser=False)
    
    logger.info("\n" + "="*60)
    logger.info("SUCCESS! Here is your NEW Refresh Token (Production Mode):")
    logger.info("="*60)
    logger.info(creds.refresh_token)
    logger.info("="*60)
    logger.info("Update your .env and GitHub Secrets with this value.")

if __name__ == '__main__':
    generate_token()
