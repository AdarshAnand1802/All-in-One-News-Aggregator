import os
import re
import glob
import json
import pandas as pd
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = filename.replace("\n", " ").replace("\r", " ").strip()
    return filename

def delete_all_images(folder):
    files = glob.glob(os.path.join(folder, '*.jpg'))
    for f in files:
        os.remove(f)
    print("Deleted all previous images.")

def scrape_toi(html_path):
    # Read HTML content from file
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_doc = f.read()
    except Exception as e:
        print(f"Error reading HTML file: {e}")
        return

    soup = BeautifulSoup(html_doc, 'html.parser')

    image_folder = 'images/TOI_images'
    os.makedirs(image_folder, exist_ok=True)
    delete_all_images(image_folder)

    output_folder = 'files/TOI'
    os.makedirs(output_folder, exist_ok=True)

    base_url = "https://timesofindia.indiatimes.com"
    each_story_divs = soup.find_all('div', class_=lambda x: x == 'col_l_6')[:24]
    stories = []

    for idx, each_story_div in enumerate(each_story_divs, start=1):
        link_tag = each_story_div.find('a', href=True)
        news_url = urljoin(base_url, link_tag['href']) if link_tag else 'No news URL'

        img = each_story_div.find('img')
        img_url = urljoin(base_url, img['src']) if img and 'src' in img.attrs else 'No image URL'
        img_alt = img['alt'] if img and 'alt' in img.attrs else 'No image alt text'

        headline = each_story_div.find('figcaption').text.strip() if each_story_div.find('figcaption') else 'No headline'
        time_element = each_story_div.find('time', class_='date-format')
        date_time = time_element['data-time'] if time_element and 'data-time' in time_element.attrs else 'No date and time'

        paragraph_element = each_story_div.find('p', class_='wrapLines l5')
        paragraph = paragraph_element.text.strip() if paragraph_element else 'No paragraph'

        story = {
            'Index': idx,
            'Image URL': img_url,
            'Image Alt Text': img_alt,
            'Headline': headline,
            'Date and Time': date_time,
            'Paragraph': paragraph,
            'Image Path': '',
            'News URL': news_url
        }

        # Save alt text to a .txt file
        if img_alt != 'No image alt text':
            alt_text_filename = os.path.join(image_folder, f"image_{idx}_alt.txt")
            with open(alt_text_filename, 'w', encoding='utf-8') as alt_file:
                alt_file.write(img_alt)
            print(f"Saved alt text for image {idx} to {alt_text_filename}")

        # Download image with error handling
        if img_url != 'No image URL':
            try:
                response = requests.get(img_url, timeout=10)
                response.raise_for_status()
                img_filename = os.path.join(image_folder, f'image_{idx}.jpg')
                with open(img_filename, 'wb') as img_file:
                    img_file.write(response.content)
                print(f"Downloaded and saved image: {img_filename}")
                story['Image Path'] = img_filename
            except requests.RequestException as e:
                print(f"Failed to download image {img_url}: {e}")

        stories.append(story)

    # Print stories
    for story in stories:
        for key, value in story.items():
            print(f"{key}: {value}")
        print("\n")

    # Save JSON
    json_path = os.path.join(output_folder, "toi_stories.json")
    with open(json_path, "w", encoding='utf-8') as f_json:
        json.dump(stories, f_json, indent=4, ensure_ascii=False)
    print(f"Saved data to {json_path}")

    # Save CSV
    csv_path = os.path.join(output_folder, "toi_stories.csv")
    df = pd.DataFrame(stories)
    df.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Saved data to {csv_path}")
