import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv

# fetch HTML with safe headers
def fetch_html(url):
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

# parse designer links from the season page
def parse_designers(base_url):
    """get all designer links from a season's page"""
    html = fetch_html(base_url)
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')

    # target links with specific classes and attributes
    designer_links = soup.select('a.NavigationInternalLink-cWEaeo.kHWqlu')

    # construct absolute URLs for each designer
    links = [urljoin(base_url, link['href']) for link in designer_links]
    return links

def save_designers_to_csv(designers, filename="test_designers_output.csv"):
    """save a list of designers to a csv file, each on a new line."""
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows([[designer] for designer in designers])  # wrap each designer in a list
    print(f"designers saved to {filename}")

def main():
    base_url = "https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear"
    print(f"Testing designer link extraction from: {base_url}")
    designers = parse_designers(base_url)
    if designers:
        print(f"found {len(designers)} designer links:")
        save_designers_to_csv(designers)  # call the save function
        for link in designers[:5]:  # print only first 5 links
            print(link)
    else:
        print("no designers found. check your selectors or url.")

if __name__ == "__main__":
    main()