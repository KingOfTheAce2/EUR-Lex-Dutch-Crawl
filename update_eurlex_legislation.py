import os
import re
import time
import requests
from bs4 import BeautifulSoup
from datasets import load_dataset, Dataset
from huggingface_hub import login

# Hugging Face setup
HF_TOKEN = os.getenv("HF_TOKEN")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN not set in environment.")
login(HF_TOKEN)

DATASET_NAME = "vGassen/EUR-Lex-Dutch"
SOURCE = "EUR-Lex"

SEARCH_BASE = "https://eur-lex.europa.eu"
START_URL = (
    "https://eur-lex.europa.eu/search.html?"
    "SUBDOM_INIT=LEGISLATION&lang=en&type=advanced&"
    "qid=1749326996678&wh0=andCOMPOSE=NLD,"
    "orEMBEDDED_MANIFESTATION-TYPE=pdf;"
    "EMBEDDED_MANIFESTATION-TYPE=pdfa1a;"
    "EMBEDDED_MANIFESTATION-TYPE=pdfa1b;"
    "EMBEDDED_MANIFESTATION-TYPE=pdfa2a;"
    "EMBEDDED_MANIFESTATION-TYPE=pdfx;"
    "EMBEDDED_MANIFESTATION-TYPE=pdf1x;"
    "EMBEDDED_MANIFESTATION-TYPE=html;"
    "EMBEDDED_MANIFESTATION-TYPE=xhtml;"
    "EMBEDDED_MANIFESTATION-TYPE=doc;"
    "EMBEDDED_MANIFESTATION-TYPE=docx"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_existing_urls():
    try:
        dataset = load_dataset(DATASET_NAME, split="train")
        return set(dataset["URL"])
    except Exception:
        return set()

def extract_celex_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    celex_links = set()

    for a in links:
        match = re.search(r"CELEX%3A([0-9A-Z]+)", a["href"])
        if match:
            celex = match.group(1)
            celex_links.add(celex)
    return list(celex_links)

def fetch_dutch_text(celex, qid):
    url = f"https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:{celex}&qid={qid}"
    res = requests.get(url, headers=HEADERS)
    if not res.ok:
        return None, None

    soup = BeautifulSoup(res.text, "html.parser")
    div = soup.find("div", {"class": "tab-content"})

    if not div:
        return None, None

    paragraphs = div.find_all("p")
    text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    return url, text

def get_search_page(page_number):
    url = f"{START_URL}&page={page_number}"
    res = requests.get(url, headers=HEADERS)
    return res.text if res.ok else None

def main():
    existing = get_existing_urls()
    new_data = []
    max_pages = 5  # TEMP: adjust as needed or implement checkpointing

    for page in range(1, max_pages + 1):
        print(f"Processing page {page}")
        html = get_search_page(page)
        if not html:
            continue

        celexes = extract_celex_links(html)
        for celex in celexes:
            nl_url = f"https://eur-lex.europa.eu/legal-content/NL/TXT/HTML/?uri=CELEX:{celex}&qid=1749326996678"
            if nl_url in existing:
                continue
            url, text = fetch_dutch_text(celex, qid="1749326996678")
            if text:
                new_data.append({
                    "URL": url,
                    "Content": text,
                    "Source": SOURCE
                })
                time.sleep(1)

    if not new_data:
        print("No new documents.")
        return

    dataset = Dataset.from_dict({
        "URL": [x["URL"] for x in new_data],
        "Content": [x["Content"] for x in new_data],
        "Source": [x["Source"] for x in new_data]
    })

    try:
        existing_dataset = load_dataset(DATASET_NAME, split="train")
        full_dataset = Dataset.from_dict({
            "URL": existing_dataset["URL"] + dataset["URL"],
            "Content": existing_dataset["Content"] + dataset["Content"],
            "Source": existing_dataset["Source"] + dataset["Source"]
        })
    except Exception:
        full_dataset = dataset

    full_dataset.push_to_hub(DATASET_NAME)
    print(f"Pushed {len(new_data)} new entries.")

if __name__ == "__main__":
    main()
