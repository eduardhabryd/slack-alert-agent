import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TokenFetcher")

def get_slack_tokens(workspace_url):
    """
    Launches Chrome to let user log in to Slack, then extracts xoxc token and d cookie.
    """
    logger.info("Launching Chrome...")
    
    # 1. Setup Chrome Driver
    # Selenium 4.6+ has built-in driver management (Selenium Manager), so no need for ChromeDriverManager.
    
    chrome_options = Options()
    
    # Use a local user-data-dir to persist the session so you only log in once per folder cleanup
    chrome_options.add_argument(f"user-data-dir={os.path.join(os.getcwd(), 'chrome_profile')}") 
    
    # Attempt to detach so it doesn't close immediately (optional)
    # chrome_options.add_experimental_option("detach", True)

    logger.info("Initializing Chrome Driver...")
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        logger.error(f"Failed to initialize driver: {e}")
        print("\nPossible fix: Try restarting your computer to clear locked Chrome processes.")
        return None, None
        
    logger.info("Browser initialized successfully.")
    
    try:
        logger.info(f"Navigating to {workspace_url}...")
        driver.get(workspace_url)
        
        print("\n" + "="*50)
        print("PLEASE LOG IN TO SLACK IN THE BROWSER WINDOW.")
        print("Once you see your chats, press ENTER here to continue extraction...")
        print("="*50 + "\n")
        input("Press Enter after logging in...")
        
        # 2. Extract Data
        # We need the 'local storage' or cookies. 
        # The 'xoxc' token is often in local storage under 'reduxPersist:...' or similar, 
        # OR we can try to find it in the 'boot_data' global variable if exposed,
        # OR we can just ask the user to find it if we can't automate it easily.
        # However, a more reliable way might be to check Cookies for 'd' and LocalStorage/SessionStorage for token.
        
        logger.info("Extracting cookies...")
        cookies = driver.get_cookies()
        d_cookie = next((c['value'] for c in cookies if c['name'] == 'd'), None)
        
        if not d_cookie:
            logger.error("Could not find 'd' cookie! Are you logged in?")
            return None, None, None

        logger.info("Extracting token and URL from Local Storage...")
        # Get token AND team URL
        result = driver.execute_script("""
            try {
               var local = localStorage.getItem('localConfig_v2');
               if (local) {
                   var parsed = JSON.parse(local);
                   if (parsed.teams) {
                       var teams = Object.values(parsed.teams);
                       if (teams.length > 0) {
                           return {
                               token: teams[0].token,
                               url: teams[0].url || teams[0].domain
                           };
                       }
                   }
               }
            } catch(e) {}
            return null;
        """)
        
        token = None
        workspace_url = None
        
        if result:
            token = result.get('token')
            workspace_url = result.get('url')
            
        if not token:
            logger.warning("Could not automatically find 'xoxc' token.")
            print("Please check Developer Tools manually.")
            token = input("Enter your xoxc- token manually: ").strip()

        if not workspace_url:
            # Try another way: checking window location if it's not app.slack.com
            current_url = driver.current_url
            if "app.slack.com" not in current_url:
                 # assume we are on the team domain
                 from urllib.parse import urlparse
                 parsed = urlparse(current_url)
                 workspace_url = f"{parsed.scheme}://{parsed.netloc}"
        
        if workspace_url and not workspace_url.startswith("http"):
             # if we got just domain
             workspace_url = f"https://{workspace_url}.slack.com"
             
        if not workspace_url:
             logger.warning("Could not determine Workspace URL.")
             workspace_url = input("Enter your Workspace URL (e.g. https://myteam.slack.com): ").strip()
        
        return token, d_cookie, workspace_url
        
    finally:
        driver.quit()

def update_env(token, cookie, url):
    env_path = ".env"
    
    # Read existing lines
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Remove existing keys
    lines = [l for l in lines if not l.startswith("SLACK_TOKEN=") and not l.startswith("SLACK_COOKIE=") and not l.startswith("SLACK_WORKSPACE_URL=")]
    
    # Ensure last line ends with newline
    if lines and not lines[-1].endswith('\n'):
        lines.extend(['\n', '\n'])
    else:
        lines.extend(['\n'])

    # Append new
    lines.append(f"SLACK_TOKEN={token}\n")
    lines.append(f"SLACK_COOKIE={cookie}\n")
    lines.append(f"SLACK_WORKSPACE_URL={url}\n")
    
    with open(env_path, "w") as f:
        f.writelines(lines)
    logger.info(f"Updated {env_path}")

if __name__ == "__main__":
    url = input("Enter Slack Workspace URL (e.g., https://app.slack.com/client/T12345): ").strip()
    if not url:
        # Default fallback
        url = "https://app.slack.com/client/T04B6PEDQ"
        
    token, cookie, workspace_url = get_slack_tokens(url)
    
    if token and cookie:
        print(f"\nFOUND CREDENTIALS!")
        print(f"Token: {token[:10]}...")
        print(f"Cookie: {cookie[:10]}...")
        print(f"URL:   {workspace_url}")
        update_env(token, cookie, workspace_url)
        print("Scuccessfully saved to .env")
    else:
        print("Failed to get credentials.")
