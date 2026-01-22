import re
import sys
import csv
import codecs
import requests
import os


def fetch_html(url):
    """fetch html from the given URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def decode_unicode(string):
    """decode unicode characters like \\u002F into readable format"""
    return codecs.decode(string, 'unicode_escape')


def extract_image_urls(html):
    """extract image IDs and URLs from html, filtering to valid collection images"""
    id_pattern = r'"id":"([^"]+)"'
    url_pattern = r'"url":"([^"]+)"'

    id_matches = list(re.finditer(id_pattern, html))
    print(f"Found {len(id_matches)} raw IDs")

    rows = []
    for index, match in enumerate(id_matches):
        id_value = match.group(1)
        start_pos = match.end()

        # find the first url after this id
        url_match = re.search(url_pattern, html[start_pos:])
        url_value = url_match.group(1) if url_match else None

        # filter: only keep valid 24-char hex IDs with urls ending in #[1-4 digits]
        is_valid_id = re.match(r"^[0-9a-f]{24}$", id_value)
        is_valid_url = url_value and re.search(r"#\d{1,4}$", url_value)
        if is_valid_id and is_valid_url:
            rows.append({
                "id": id_value,
                "url": decode_unicode(url_value),
                "image_url": f"https://assets.vogue.com/photos/{id_value}/master/"
            })

    # count by category
    categories = {"collection": 0, "details": 0, "beauty": 0, "front-row": 0}
    for row in rows:
        for cat in categories:
            if cat in row["url"]:
                categories[cat] += 1
                break

    print(f"Extracted {len(rows)} valid image URLs:")
    for cat, count in categories.items():
        if count > 0:
            print(f"  {cat}: {count}")

    return rows


def save_csv(rows, season, designer):
    """save extracted data to csv in the output folder"""
    output_folder = os.path.join(os.path.dirname(__file__), "..", "output", season, designer)
    os.makedirs(output_folder, exist_ok=True)
    filepath = os.path.join(output_folder, "images.csv")

    fieldnames = ["id", "url", "image_url"]
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved to {filepath}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_collection.py <season> <designer>")
        print("Example: python extract_collection.py spring-2012-ready-to-wear jil-sander")
        sys.exit(1)

    season = sys.argv[1]
    designer = sys.argv[2]
    url = f"https://www.vogue.com/fashion-shows/{season}/{designer}/slideshow/collection#1"

    html = fetch_html(url)
    if not html:
        return

    rows = extract_image_urls(html)
    if not rows:
        print("No images found.")
        return

    save_csv(rows, season, designer)


if __name__ == "__main__":
    main()
