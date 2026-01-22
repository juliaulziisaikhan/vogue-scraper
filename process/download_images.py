import os
import sys
import csv
import requests
from tqdm import tqdm


def download_images(input_csv, output_folder, sample=None):
    """download images from csv and organize by category"""
    categories = ["collection", "details", "beauty", "front-row"]

    os.makedirs(output_folder, exist_ok=True)

    # group rows by category
    categorized = {cat: [] for cat in categories}

    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for cat in categories:
                if cat in row["url"]:
                    categorized[cat].append(row)
                    break

    # download each category
    for category, rows in categorized.items():
        # limit to sample size if specified
        if sample:
            rows = rows[:sample]
        if not rows:
            continue

        cat_folder = os.path.join(output_folder, category)
        os.makedirs(cat_folder, exist_ok=True)

        skipped = 0
        failed = 0

        for row in tqdm(rows, desc=category, unit="img"):
            image_path = os.path.join(cat_folder, f"{row['id']}.jpg")

            # skip if already downloaded
            if os.path.exists(image_path):
                skipped += 1
                continue

            try:
                response = requests.get(row["image_url"], stream=True)
                response.raise_for_status()

                with open(image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

            except requests.exceptions.RequestException as e:
                failed += 1
                tqdm.write(f"failed: {row['image_url']}: {e}")

        print(f"  {category}: {len(rows)} total, {skipped} skipped, {failed} failed")


def main():
    if len(sys.argv) < 3:
        print("Usage: python download_images.py <season> <designer> [sample]")
        print("Example: python download_images.py spring-2012-ready-to-wear jil-sander")
        print("Example: python download_images.py spring-2012-ready-to-wear jil-sander 5")
        sys.exit(1)

    season = sys.argv[1]
    designer = sys.argv[2]
    sample = int(sys.argv[3]) if len(sys.argv) > 3 else None

    base_path = os.path.join(os.path.dirname(__file__), "..", "output", season, designer)
    input_csv = os.path.join(base_path, "images.csv")
    output_folder = os.path.join(base_path, "images")

    if sample:
        print(f"Sample mode: downloading {sample} images per category")

    download_images(input_csv, output_folder, sample)


if __name__ == "__main__":
    main()
