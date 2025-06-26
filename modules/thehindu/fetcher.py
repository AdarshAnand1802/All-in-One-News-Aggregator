import os
import requests

def fetch_and_save_to_file(url, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        r = requests.get(url)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(r.text)
        print(f"Fetched and saved content from {url} to {path}")
    except Exception as e:
        print(f"Error: {e}")
