import os
import json
import re
from bs4 import BeautifulSoup

INPUT_DIR = 'Dutch Legislation'
OUTPUT_DIR = 'Output'
SOURCE = 'EUR LEX'

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_url_from_text(text):
    # Simple regex to find a URL in the text
    match = re.search(r'https?://\S+', text)
    return match.group(0) if match else None

def strip_html_tags(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

for root, _, files in os.walk(INPUT_DIR):
    for filename in files:
        if filename.lower().endswith('.html'):
            file_path = os.path.join(root, filename)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            text_content = strip_html_tags(html_content)
            url = extract_url_from_text(html_content) or file_path.replace('\\', '/')
            output_data = {
                'url': url,
                'content': text_content,
                'source': SOURCE
            }
            # Output file name: same as input but with .json extension, in OUTPUT_DIR
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump(output_data, out_f, ensure_ascii=False, indent=2)
