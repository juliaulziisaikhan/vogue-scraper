import csv
import re
import codecs
import os


def decode_unicode(string):
    """decode unicode characters like \\u002F into readable format"""
    return codecs.decode(string, 'unicode_escape')


def write_csv(filename, rows, fieldnames):
    """write rows to a csv file in the output folder"""
    # define the output directory path
    output_folder = os.path.join(os.path.dirname(__file__), "..", "output")
    # ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    # construct the full path for the csv file
    filepath = os.path.join(output_folder, filename)

    # write the csv
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"output saved to {filepath}")


def process_csv(input_file, output_file):
    """process id_url_srcset.csv to filter, clean data, and add image_url"""
    rows = []

    # read and filter rows
    with open(input_file, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # check if url ends with #[1-4 digits]
            if re.search(r"#\d{1,4}$", row["url"]):
                # decode unicode in url
                row["url"] = decode_unicode(row["url"])
                # add image_url
                row["image_url"] = f"https://assets.vogue.com/photos/{row['id']}/master/"
                rows.append(
                    {"index": row["index"], "id": row["id"], "url": row["url"], "image_url": row["image_url"]}
                )

    # write filtered rows to new csv
    if rows:
        fieldnames = ["index", "id", "url", "image_url"]
        write_csv(output_file, rows, fieldnames)

    print(f"processed {len(rows)} rows.")


if __name__ == "__main__":
    # include the relative path to the file
    input_csv = "../output/test_raw_collection_output.csv"  # input file
    output_csv = "test_process_collection_output.csv"  # output file
    process_csv(input_csv, output_csv)
