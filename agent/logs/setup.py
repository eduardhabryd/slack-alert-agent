import logging
import sys
from agent.config.schema import LoggingConfig

def setup_logging(config: LoggingConfig):
    # Convert string level to logging constant
    level = getattr(logging, config.level.upper(), logging.INFO)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
