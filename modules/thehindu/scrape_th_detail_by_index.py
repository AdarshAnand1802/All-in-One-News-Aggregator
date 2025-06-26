import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

def fetch_html(url, path):
    """Fetch the HTML page for a given news article."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(path, "w", encoding='utf-8') as f:
            f.write(response.text)
        print(f"[INFO] Saved HTML to {path}")
    except Exception as e:
        print(f"[ERROR] Failed to fetch HTML: {e}")

def scrape_single_th_article(index, json_path="files/TH/th_stories.json", csv_path="files/TH/th_stories.csv"):
    # Load all stories
    with open(json_path, "r", encoding='utf-8') as f:
        stories = json.load(f)

    # Match by "Index" key
    story = next((s for s in stories if s["Index"] == index), None)
    if story is None:
        print(f"[ERROR] No story found for index {index}")
        return

    news_url = story.get("News URL", "")
    if not news_url.startswith("http"):
        print(f"[ERROR] Invalid News URL for index {index}")
        return

    # Fetch and save HTML
    os.makedirs("temp", exist_ok=True)
    html_path = "temp/NewsDescription.html"
    fetch_html(news_url, html_path)

    # Parse the HTML
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Extract headline
    headline_tag = soup.find("h1")
    if headline_tag:
        story["Headline"] = headline_tag.get_text(strip=True)

    # Extract article paragraph
    article_div = soup.find("div", class_="articlebodycontent")
    if article_div:
        for tag in article_div(["style", "script", "div"]):
            tag.decompose()
        for br in article_div.find_all("br"):
            br.replace_with("\n")
        paragraph_text = article_div.get_text(separator="\n", strip=True)
        if paragraph_text:
            print("\n[DEBUG] Extracted full article text:\n")
            print(paragraph_text)
            story["Paragraph"] = paragraph_text

    # Extract image
    img_url = ""
    img_alt = "No alt text"
    picture_tag = soup.select_one("div.article-picture picture")
    if picture_tag:
        source_tag = picture_tag.find("source", srcset=True)
        if source_tag:
            img_url = source_tag["srcset"]
        img_tag = picture_tag.find("img")
        if img_tag and img_tag.get("alt"):
            img_alt = img_tag["alt"]

    if img_url:
        story["Image URL"] = img_url
        story["Image Alt Text"] = img_alt
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            image_folder = "images/TH_images"
            os.makedirs(image_folder, exist_ok=True)
            img_filename = os.path.join(image_folder, f"image_{index}.jpg")
            with open(img_filename, 'wb') as img_file:
                img_file.write(response.content)
            story["Image Path"] = img_filename
            print(f"[INFO] Downloaded and replaced updated image: {img_filename}")
        except Exception as e:
            print(f"[WARNING] Could not download image: {e}")

    # Extract date and time
    datetime_span = soup.select_one("div.update-publish-time p.updated-time span")
    if datetime_span:
        story["Date and Time"] = datetime_span.get_text(strip=True)

    # Replace updated story
    for i, s in enumerate(stories):
        if s["Index"] == index:
            stories[i] = story
            break

    # Save to JSON
    with open(json_path, "w", encoding='utf-8') as f_json:
        json.dump(stories, f_json, indent=4, ensure_ascii=False)

    # Save to CSV
    pd.DataFrame(stories).to_csv(csv_path, index=False, encoding='utf-8')
    print(f"[SUCCESS] Updated story at index {index} in JSON and CSV.")

    # Clean temp file
    try:
        os.remove(html_path)
        print(f"[INFO] Deleted temporary file: {html_path}")
    except Exception as e:
        print(f"[WARNING] Could not delete temp file: {e}")

