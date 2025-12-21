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
    config = AppConfig(**raw_config)

    # Apply environment variable overrides (common pattern for secrets)
    # These are critical for secrets that shouldn't be in config.yaml
    
    # Telegram Username override
    env_tg_user = os.getenv("TELEGRAM_USERNAME")
    if env_tg_user:
        config.telegram.call.username = env_tg_user

    return config
