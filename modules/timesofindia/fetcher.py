import os
import requests

def fetch_and_save_to_file(url, path):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"Directory created or already exists: {os.path.dirname(path)}")

        r = requests.get(url)
        r.raise_for_status()

        with open(path, 'w', encoding='utf-8') as f:
            f.write(r.text)
        print(f"Content written to file: {path}")

    except Exception as e:
        print(f"An error occurred in fetch_and_save_to_file: {e}")
