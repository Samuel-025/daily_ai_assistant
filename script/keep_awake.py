# scripts/keep_awake.py
import os
import requests
import sys

def keep_streamlit_awake():
    streamlit_url = os.getenv('STREAMLIT_URL')
    
    if not streamlit_url:
        print("Error: STREAMLIT_URL environment variable not set")
        sys.exit(1)
    
    try:
        response = requests.get(streamlit_url, timeout=10)
        if response.status_code == 200:
            print(f"Successfully pinged Streamlit app at {streamlit_url}")
        else:
            print(f"Warning: Received status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error pinging Streamlit app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    keep_streamlit_awake()
