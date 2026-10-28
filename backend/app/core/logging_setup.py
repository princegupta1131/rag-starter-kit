"""Plain, readable logs. Level comes from LOG_LEVEL in .env."""
import logging

from app.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # quieten chatty libraries
    for name in ("httpx", "httpcore", "google_genai", "openai", "psycopg.pool"):
        logging.getLogger(name).setLevel(logging.WARNING)
