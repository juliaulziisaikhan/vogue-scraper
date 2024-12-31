import csv
import re
import codecs


def decode_unicode(string):
    """decode unicode characters like \\u002F into readable format"""
    return codecs.decode(string, 'unicode_escape')


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
                rows.append({"index": row["index"], "id": row["id"], "url": row["url"], "image_url": row["image_url"]})

    # write filtered rows to new csv (exclude srcset column)
    if rows:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["index", "id", "url", "image_url"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    print(f"Processed {len(rows)} rows. Output saved to {output_file}.")


if __name__ == "__main__":
    input_csv = "id_url_srcset.csv"  # input file
    output_csv = "processed_id_image_url.csv"  # output file
    process_csv(input_csv, output_csv)
