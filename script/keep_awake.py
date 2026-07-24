import os
import requests

# Get the Streamlit URL from environment variable
streamlit_url = os.getenv("STREAMLIT_URL")

if not streamlit_url:
    print("Error: STREAMLIT_URL environment variable not set")
    exit(1)

try:
    response = requests.get(streamlit_url, timeout=10)
    print(f"Successfully pinged Streamlit app. Status code: {response.status_code}")
except Exception as e:
    print(f"Error pinging Streamlit app: {e}")
    exit(1)
