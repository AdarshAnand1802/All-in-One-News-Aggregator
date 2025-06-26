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

def scrape_single_et_article(index, json_path="files/ET/et_stories.json", csv_path="files/ET/et_stories.csv"):
    # Load all stories
    with open(json_path, "r", encoding='utf-8') as f:
        stories = json.load(f)

    # Match by "Index" key in story
    story = next((s for s in stories if s["Index"] == index), None)
    if story is None:
        print(f"[ERROR] No story found for index {index}")
        return

    news_url = story.get("News URL", "")
    if not news_url.startswith("http"):
        print(f"[ERROR] Invalid News URL for index {index}")
        return

    # Fetch and save the article HTML
    os.makedirs("temp", exist_ok=True)
    html_path = "temp/NewsDescription.html"
    fetch_html(news_url, html_path)

    # Parse the HTML
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # Headline from <h1>
    headline_tag = soup.find("h1")
    story["Headline"] = headline_tag.get_text(strip=True) if headline_tag else story["Headline"]

    # Paragraph from <div class="artText">
    article_div = soup.find("div", class_="artText")
    if article_div:
        # Remove all styles, scripts, and inner divs (ads, widgets)
        for tag in article_div(["style", "script", "div"]):
            tag.decompose()

        # Replace <br> with newline
        for br in article_div.find_all("br"):
            br.replace_with("\n")

        paragraph_text = article_div.get_text(separator="\n", strip=True)

        if paragraph_text:
            print("\n[DEBUG] Extracted full article text:\n")
            print(paragraph_text)
            story["Paragraph"] = paragraph_text

    # Image from <div class="imgBox"><figure class="artImg"><img ...>
    img_tag = soup.select_one("div.imgBox figure.artImg img")
    img_url = ""

    if img_tag and img_tag.get("src"):
        img_url = urljoin(news_url, img_tag["src"])
        story["Image URL"] = img_url
        story["Image Alt Text"] = img_tag.get("alt", "No alt text")

        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()
            image_folder = "images/ET_images"
            os.makedirs(image_folder, exist_ok=True)
            img_filename = os.path.join(image_folder, f"image_{index}.jpg")  # overwrite original image
            with open(img_filename, 'wb') as img_file:
                img_file.write(response.content)
            story["Image Path"] = img_filename  # keep path consistent for GUI
            print(f"[INFO] Downloaded and replaced updated image: {img_filename}")
        except Exception as e:
            print(f"[WARNING] Could not download image: {e}")

    # Replace the updated story back into the list
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

    # Delete temp HTML file
    try:
        os.remove(html_path)
        print(f"[INFO] Deleted temporary file: {html_path}")
    except Exception as e:
        print(f"[WARNING] Could not delete temp file: {e}")

