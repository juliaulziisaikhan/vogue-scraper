import os
import sys
import time
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_html(url):
    """fetch html from the given URL"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(2)  # throttle requests
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_designers(season_url):
    """get all designer links from a season's page"""
    html = fetch_html(season_url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    designer_links = soup.select('a.grouped-navigation__link')
    links = [urljoin(season_url, link['href']) for link in designer_links]
    return links


def save_csv(designers, season):
    """save designer links to csv"""
    output_folder = os.path.join(os.path.dirname(__file__), "..", "output", season)
    os.makedirs(output_folder, exist_ok=True)
    filepath = os.path.join(output_folder, "designers.csv")

    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["designer_url"])
        writer.writerows([[d] for d in designers])
    print(f"Saved {len(designers)} designers to {filepath}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_designers.py <season>")
        print("Example: python extract_designers.py spring-2012-ready-to-wear")
        sys.exit(1)

    season = sys.argv[1]
    season_url = f"https://www.vogue.com/fashion-shows/{season}"

    designers = extract_designers(season_url)
    if not designers:
        print("No designers found.")
        return

    save_csv(designers, season)


if __name__ == "__main__":
    main()
