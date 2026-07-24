# script/keep_awake.py
import os
import time
import requests
import sys

MAX_ATTEMPTS = 3
INITIAL_DELAY_SECONDS = 15  # doubles after each failed attempt
REQUEST_TIMEOUT_SECONDS = 30  # sleeping Streamlit apps can be slow to wake


def keep_streamlit_awake():
    streamlit_url = os.getenv('STREAMLIT_URL')

    if not streamlit_url:
        print("Error: STREAMLIT_URL environment variable not set")
        sys.exit(1)

    delay = INITIAL_DELAY_SECONDS

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(streamlit_url, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 200:
                print(f"Successfully pinged Streamlit app at {streamlit_url} (attempt {attempt}/{MAX_ATTEMPTS})")
                return
            else:
                print(f"Attempt {attempt}/{MAX_ATTEMPTS}: received status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt}/{MAX_ATTEMPTS}: error pinging Streamlit app: {e}")

        if attempt < MAX_ATTEMPTS:
            print(f"Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # exponential backoff

    print(f"Failed to ping Streamlit app at {streamlit_url} after {MAX_ATTEMPTS} attempts")
    sys.exit(1)


if __name__ == "__main__":
    keep_streamlit_awake()