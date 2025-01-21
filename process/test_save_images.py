import csv
import os
import requests


def save_images_from_csv(input_csv, output_folder):
    """download and save images from image_url column in csv into categorized folders"""
    # mapping suffixes to folder names
    categories = ["collection", "details", "beauty", "front-row"]

    # ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # organize rows by category
    categorized_rows = {category: [] for category in categories}

    with open(input_csv, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            for category in categories:
                if category in row["url"]:  # check if the suffix matches the category
                    categorized_rows[category].append(row)
                    break

    # process each category
    for category, rows in categorized_rows.items():
        if rows:
            category_folder = os.path.join(output_folder, category)
            os.makedirs(category_folder, exist_ok=True)  # create category folder

            total = len(rows)
            for idx, row in enumerate(rows, start=1):
                image_url = row["image_url"]
                image_id = row["id"]  # use the id column for unique filenames
                image_path = os.path.join(category_folder, f"{image_id}.jpg")

                try:
                    # download the image
                    response = requests.get(image_url, stream=True)
                    response.raise_for_status()  # raise an error for bad status codes

                    # save the image
                    with open(image_path, "wb") as image_file:
                        for chunk in response.iter_content(1024):
                            image_file.write(chunk)

                    print(f"saving {idx}/{total} {category}")

                except requests.exceptions.RequestException as e:
                    print(f"failed to download {image_url}: {e}")

            print(f"{category} saved")


if __name__ == "__main__":
    input_csv = "../output/test_process_collection_output.csv"  # path to your input csv
    output_folder = "../output/images"  # main folder to save images

    save_images_from_csv(input_csv, output_folder)
