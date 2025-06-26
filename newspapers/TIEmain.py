import sys
import os

# Add project root directory (NEWSAPP) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from modules.indianexpress.fetcher import fetch_and_save_to_file
from modules.indianexpress.scraper import scrape_ie

def main():
    url = "https://indianexpress.com/section/india/"
    html_path = "data/IE/TIE.html"

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(html_path), exist_ok=True)

    try:
        print("[INFO] Fetching data from Indian Express...")
        fetch_and_save_to_file(url, html_path)
        print(f"[INFO] HTML content saved to {html_path}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
        return

    try:
        print("[INFO] Starting to scrape content...")
        scrape_ie(html_path)
        print("[INFO] Scraping completed successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to scrape data: {e}")

if __name__ == "__main__":
    main()
