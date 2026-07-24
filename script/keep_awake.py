import os
import time
import logging
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

STREAMLIT_URL = os.environ.get("STREAMLIT_URL")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def ping_app():
    if not STREAMLIT_URL:
        logger.error("STREAMLIT_URL environment variable is not set")
        raise SystemExit(1)

    headers = {"User-Agent": USER_AGENT}
    pages = [STREAMLIT_URL.rstrip("/"), f"{STREAMLIT_URL.rstrip('/')}/"]

    for page in pages:
        try:
            logger.info("Visiting %s", page)
            response = requests.get(page, headers=headers, timeout=30)
            logger.info("Status: %d | Length: %d bytes", response.status_code, len(response.content))
            response.raise_for_status()
            time.sleep(2)
        except requests.RequestException as e:
            logger.error("Failed to reach %s: %s", page, e)
            raise SystemExit(1)


if __name__ == "__main__":
    ping_app()