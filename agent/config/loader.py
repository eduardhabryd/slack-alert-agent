import os
import yaml
from typing import Optional
from dotenv import load_dotenv
from agent.config.schema import AppConfig

CONFIG_PATH = "config.yaml"

def load_config(path: str = CONFIG_PATH) -> AppConfig:
    """
    Load configuration from a YAML file and apply environment variable overrides.
    Returns a validated AppConfig object.
    """
    # Load environment variables from .env file if present
    load_dotenv()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found at {path}")

    with open(path, "r") as f:
        raw_config = yaml.safe_load(f) or {}

    # Validate against schema
    # We can't validate fully yet if we depend on env vars for some fields that are missing in yaml
    # So we might need to inject env vars BEFORE validation or make them optional in schema and validate later.
    # For now, let's assume raw_config is partial and we patch it.
    
    # Patch in Slack secrets from Env if not in YAML
    if raw_config.get("mode") == "api" or os.getenv("SLACK_TOKEN"):
        if "slack" not in raw_config:
            raw_config["slack"] = {}
        
        if os.getenv("SLACK_TOKEN"):
            raw_config["slack"]["token"] = os.getenv("SLACK_TOKEN")
        if os.getenv("SLACK_COOKIE"):
            raw_config["slack"]["cookie"] = os.getenv("SLACK_COOKIE")
        if os.getenv("SLACK_WORKSPACE_URL"):
            raw_config["slack"]["workspace_url"] = os.getenv("SLACK_WORKSPACE_URL")
            
        # Ensure workspace_url is present if mode is api
        if "workspace_url" not in raw_config["slack"]:
             # This might fail validation if not provided in YAML or here. 
             # We rely on user providing it in YAML for now.
             pass

    config = AppConfig(**raw_config)

    # Apply environment variable overrides (common pattern for secrets)
    # These are critical for secrets that shouldn't be in config.yaml
    
    # Telegram Username override
    env_tg_user = os.getenv("TELEGRAM_USERNAME")
    if env_tg_user:
        config.notifications.telegram.call.username = env_tg_user

    # Pushover overrides
    env_pushover_user = os.getenv("PUSHOVER_USER_KEY")
    if env_pushover_user:
        config.notifications.pushover.user_key = env_pushover_user
        
    env_pushover_token = os.getenv("PUSHOVER_API_TOKEN")
    if env_pushover_token:
        config.notifications.pushover.api_token = env_pushover_token
        
    # Working Hours overrides
    env_start_hours = os.getenv("WORKING_HOURS_START")
    if env_start_hours:
        config.working_hours.start = env_start_hours
        
    env_end_hours = os.getenv("WORKING_HOURS_END")
    if env_end_hours:
        config.working_hours.end = env_end_hours

    env_days = os.getenv("WORKING_HOURS_DAYS")
    if env_days:
        try:
            # Parse comma-separated string: "0,1,2" -> [0, 1, 2]
            days_list = [int(d.strip()) for d in env_days.split(",") if d.strip()]
            config.working_hours.days = days_list
        except ValueError:
            # Fallback or log warning? For now just ignore invalid format to avoid crash, 
            # or maybe logging warning is better but we don't have logger here easily accessible 
            # (unless we import it). Main catches exceptions though.
            raise ValueError(f"Invalid format for WORKING_HOURS_DAYS: {env_days}. Expected comma-separated integers (e.g., '0,1,2').")

    return config
