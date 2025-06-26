import requests
from bs4 import BeautifulSoup
import os
import re
import glob
import json
import pandas as pd
from urllib.parse import urljoin

def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    return filename.replace("\n", " ").replace("\r", " ").strip()

def delete_all_images(folder):
    files = glob.glob(os.path.join(folder, '*.jpg'))
    for f in files:
        os.remove(f)
    print(f"Deleted old images in {folder}")

def scrape_th(html_path):
    with open(html_path, "r", encoding='utf-8') as f:
        html_doc = f.read()

    soup = BeautifulSoup(html_doc, 'html.parser')

    image_folder = 'images/TH_images'
    output_folder = 'files/TH'
    os.makedirs(image_folder, exist_ok=True)
    delete_all_images(image_folder)
    os.makedirs(output_folder, exist_ok=True)

    base_url = "https://www.thehindu.com"
    each_story_divs = soup.find_all('div', class_='element row-element')[:14]
    stories = []

    for idx, each_story_div in enumerate(each_story_divs, start=1):
        link_tag = each_story_div.find('a', href=True)
        news_url = urljoin(base_url, link_tag['href']) if link_tag else 'No news URL'

        img = each_story_div.find('img')
        img_url = urljoin(base_url, img['src']) if img and 'src' in img.attrs else 'No image URL'
        img_alt = img['alt'] if img and 'alt' in img.attrs else 'No image alt text'

        headline_tag = each_story_div.find(['h2', 'h3'])
        headline = re.sub(r'[\n\t]+', ' ', headline_tag.text).strip() if headline_tag else 'No headline'

        date_tag = each_story_div.find('span', class_='dateline') or each_story_div.find('div', class_='dateline')
        date_time = date_tag.text.strip() if date_tag else 'No date and time'

        paragraph_element = each_story_div.find('p')
        paragraph = re.sub(r'[\n\t]+', ' ', paragraph_element.text).strip() if paragraph_element else 'No paragraph'

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

        if img_alt != 'No image alt text':
            alt_text_filename = os.path.join(image_folder, f"image_{idx}_alt.txt")
            with open(alt_text_filename, 'w', encoding='utf-8') as alt_file:
                alt_file.write(img_alt)
            print(f"Saved alt text for image {idx} to {alt_text_filename}")

        if img_url != 'No image URL':
            try:
                response = requests.get(img_url, timeout=10)
                response.raise_for_status()
                img_filename = os.path.join(image_folder, f'image_{idx}.jpg')
                with open(img_filename, 'wb') as img_file:
                    img_file.write(response.content)
                story['Image Path'] = img_filename
                print(f"Downloaded: {img_filename}")
            except requests.RequestException as e:
                print(f"Image download failed: {e}")

        stories.append(story)

    for story in stories:
        print(json.dumps(story, indent=2, ensure_ascii=False))

    json_path = os.path.join(output_folder, "th_stories.json")
    with open(json_path, "w", encoding='utf-8') as f_json:
        json.dump(stories, f_json, indent=4, ensure_ascii=False)

    csv_path = os.path.join(output_folder, "th_stories.csv")
    pd.DataFrame(stories).to_csv(csv_path, index=False, encoding='utf-8')

    print(f"Saved to {json_path} and {csv_path}")
