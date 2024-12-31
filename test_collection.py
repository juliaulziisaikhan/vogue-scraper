import re
import csv
import requests


def fetch_and_save_html(url, file_name):
    """fetch html from the given URL and save it to a file"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        print(f"Fetching: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"HTML saved to {file_name}")
        return file_name
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_id_url_srcset(html):
    """extract id, url, and srcset values from html"""
    # pattern to capture id, url, and srcset
    id_pattern = r'"id":"([^"]+)"'
    url_pattern = r'"url":"([^"]+)"'
    srcset_pattern = r'"srcset":"([^"]+)"'

    # find all id matches
    id_matches = list(re.finditer(id_pattern, html))
    print(f"Extracted {len(id_matches)} 'id' occurrences.")

    # initialize rows
    rows = []

    # iterate through ids and look for subsequent url and srcset
    for index, match in enumerate(id_matches):
        id_value = match.group(1)
        start_pos = match.end()  # start searching after the id match

        # find the first url after this id
        url_match = re.search(url_pattern, html[start_pos:])
        url_value = url_match.group(1) if url_match else None

        # find the first srcset after this id
        srcset_match = re.search(srcset_pattern, html[start_pos:])
        srcset_value = srcset_match.group(1) if srcset_match else None

        # append row
        rows.append({
            "index": index,
            "id": id_value,
            "url": url_value,
            "srcset": srcset_value
        })

    return rows


def parse_to_csv(rows, output_file):
    """save extracted data to csv"""
    fieldnames = ["index", "id", "url", "srcset"]
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV written to {output_file}, with {len(rows)} rows.")


def main():
    # Step 1: Fetch and save HTML
    url = "https://www.vogue.com/fashion-shows/spring-2012-ready-to-wear/jil-sander/slideshow/collection#1"
    html_file = "spring-2012-ready-to-wear-jil-sander.html"
    if not fetch_and_save_html(url, html_file):
        print("Failed to fetch and save HTML.")
        return

    # Step 2: Extract id, url, and srcset from the saved HTML file
    with open(html_file, "r", encoding="utf-8") as file:
        html = file.read()

    rows = extract_id_url_srcset(html)
    if not rows:
        print("No data extracted.")
        return

    # Step 3: Save extracted data to CSV
    output_csv = "id_url_srcset.csv"
    parse_to_csv(rows, output_csv)


if __name__ == "__main__":
    main()
