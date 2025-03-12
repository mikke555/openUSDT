from datetime import datetime
from sys import stderr

from loguru import logger

LOG_OUTPUT = f"./logs/{datetime.today().strftime('%Y-%m-%d')}.log"
LOG_ROTATION = "50 MB"

logger.remove()
logger.add(
    stderr,
    format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>",
)

logger.add(
    sink=LOG_OUTPUT,
    rotation=LOG_ROTATION,
    format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>",
)
