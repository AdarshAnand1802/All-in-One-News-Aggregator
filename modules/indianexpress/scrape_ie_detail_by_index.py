import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

def fetch_html(url, path):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, "w", encoding='utf-8') as f:
            f.write(response.text)
        print(f"[INFO] Saved HTML to {path}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch HTML: {e}")

def scrape_single_ie_article(index, json_path="files/IE/ie_stories.json", csv_path="files/IE/ie_stories.csv"):
    # Load all stories
    with open(json_path, "r", encoding='utf-8') as f:
        stories = json.load(f)

    # Get the story for the index
    story = next((s for s in stories if s["Index"] == index), None)
    if not story:
        print(f"[ERROR] No story found at index {index}")
        return

    news_url = story.get("News URL", "")
    if not news_url.startswith("http"):
        print(f"[ERROR] Invalid URL at index {index}")
        return

    # Download HTML and parse
    os.makedirs("temp", exist_ok=True)
    html_path = "temp/NewsDescription.html"
    fetch_html(news_url, html_path)

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Headline
    h1 = soup.find("h1")
    if h1:
        story["Headline"] = h1.get_text(strip=True)

    # Paragraphs: from full-content and premium-content
    paragraphs = []

    main_div = soup.find("div", id="pcl-full-content", class_="story_details")
    if main_div:
        paragraphs += [p.get_text(strip=True) for p in main_div.find_all("p")]

    premium_block = soup.find("div", class_="ev-meter-content ie-premium-content-block")
    if premium_block:
        paragraphs += [p.get_text(strip=True) for p in premium_block.find_all("p")]

    full_paragraph = "\n\n".join(p for p in paragraphs if p.strip())
    if full_paragraph:
        print("\n[DEBUG] Extracted Paragraph:\n")
        print(full_paragraph)
        story["Paragraph"] = full_paragraph

    # Image extraction from <span class="custom-caption"><img src=...>
    img_tag = soup.select_one("span.custom-caption img")
    if img_tag and img_tag.get("src"):
        img_url = urljoin(news_url, img_tag["src"])
        story["Image URL"] = img_url
        story["Image Alt Text"] = img_tag.get("alt", "No alt text")

        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            image_folder = "images/IE_images"
            os.makedirs(image_folder, exist_ok=True)
            img_filename = os.path.join(image_folder, f"image_{index}.jpg")
            with open(img_filename, 'wb') as f_img:
                f_img.write(response.content)
            story["Image Path"] = img_filename
            print(f"[INFO] Downloaded and saved new image: {img_filename}")
        except Exception as e:
            print(f"[WARNING] Could not download image: {e}")

    # Update story in list
    for i, s in enumerate(stories):
        if s["Index"] == index:
            stories[i] = story
            break

    # Save updated JSON and CSV
    with open(json_path, "w", encoding="utf-8") as f_json:
        json.dump(stories, f_json, indent=4, ensure_ascii=False)

    pd.DataFrame(stories).to_csv(csv_path, index=False, encoding='utf-8')
    print(f"[SUCCESS] Updated index {index} in JSON and CSV.")

    try:
        os.remove(html_path)
        print(f"[INFO] Deleted temp HTML: {html_path}")
    except Exception as e:
        print(f"[WARNING] Could not delete temp file: {e}")

# scrape_single_ie_article(3)