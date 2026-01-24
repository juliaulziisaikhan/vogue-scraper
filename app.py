import os
import json
import csv
import random
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, jsonify, request, Response, send_from_directory

# Import functions from existing scripts
from process.extract_collection import fetch_html, extract_image_urls, save_csv

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SEASONS_FILE = os.path.join(OUTPUT_DIR, "seasons.json")
DESIGNERS_FILE = os.path.join(OUTPUT_DIR, "designers.json")


def fetch_seasons_from_vogue():
    """Fetch all available seasons from Vogue's website"""
    url = "https://www.vogue.com/fashion-shows/seasons"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=re.compile(r'/fashion-shows/[a-z]+-\d{4}'))

    seasons = set()
    for link in links:
        href = link.get('href', '')
        match = re.search(r'/fashion-shows/([a-z]+-\d{4}[a-z-]*)', href)
        if match:
            seasons.add(match.group(1))

    return sorted(seasons, reverse=True)


def get_seasons_by_year(seasons_list):
    """Organize seasons by year"""
    by_year = {}
    for season in seasons_list:
        match = re.search(r'(\d{4})', season)
        if match:
            year = match.group(1)
            if year not in by_year:
                by_year[year] = []
            by_year[year].append(season)

    # Sort years descending, seasons within each year alphabetically
    sorted_years = sorted(by_year.keys(), reverse=True)
    return {year: sorted(by_year[year]) for year in sorted_years}


def load_seasons_cache():
    """Load seasons from cache file"""
    if os.path.exists(SEASONS_FILE):
        with open(SEASONS_FILE, 'r') as f:
            return json.load(f)
    return None


def save_seasons_cache(seasons_list):
    """Save seasons to cache file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = {
        "seasons": seasons_list,
        "by_year": get_seasons_by_year(seasons_list)
    }
    with open(SEASONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def fetch_designers_from_vogue(season):
    """Fetch all designers for a season from Vogue's website"""
    url = f"https://www.vogue.com/fashion-shows/{season}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    # Try multiple selectors for different page layouts
    designers = set()

    # Method 1: grouped-navigation__link (older pages)
    for link in soup.select('a.grouped-navigation__link'):
        href = link.get('href', '')
        match = re.search(r'/fashion-shows/[^/]+/([^/]+)', href)
        if match:
            designers.add(match.group(1))

    # Method 2: Any link containing the season path with a designer slug
    if not designers:
        for link in soup.find_all('a', href=re.compile(f'/fashion-shows/{re.escape(season)}/[^/]+')):
            href = link.get('href', '')
            match = re.search(r'/fashion-shows/[^/]+/([^/]+)', href)
            if match and match.group(1) not in ['slideshow', 'reviews', 'details', 'beauty', 'front-row']:
                designers.add(match.group(1))

    return sorted(designers)


def load_designers_cache():
    """Load designers cache from file"""
    if os.path.exists(DESIGNERS_FILE):
        with open(DESIGNERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_designers_cache(cache):
    """Save designers cache to file"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(DESIGNERS_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def get_collections():
    """Get all downloaded collections with image counts and random thumbnail"""
    collections = []

    if not os.path.exists(OUTPUT_DIR):
        return collections

    for season in os.listdir(OUTPUT_DIR):
        season_path = os.path.join(OUTPUT_DIR, season)
        if not os.path.isdir(season_path) or season.startswith('.'):
            continue

        for designer in os.listdir(season_path):
            designer_path = os.path.join(season_path, designer)
            if not os.path.isdir(designer_path) or designer.startswith('.'):
                continue

            # Count unique image IDs in CSV
            csv_path = os.path.join(designer_path, "images.csv")
            csv_count = 0
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    unique_ids = set(row['id'] for row in reader)
                    csv_count = len(unique_ids)

            # Count downloaded images and collect all image paths
            images_path = os.path.join(designer_path, "images")
            downloaded = 0
            all_images = []
            if os.path.exists(images_path):
                for cat in os.listdir(images_path):
                    cat_path = os.path.join(images_path, cat)
                    if os.path.isdir(cat_path):
                        for f in os.listdir(cat_path):
                            if f.endswith('.jpg'):
                                downloaded += 1
                                all_images.append(f"/images/{season}/{designer}/{cat}/{f}")

            # Pick a random thumbnail
            thumbnail = random.choice(all_images) if all_images else None

            collections.append({
                "season": season,
                "designer": designer,
                "urls_extracted": csv_count,
                "images_downloaded": downloaded,
                "thumbnail": thumbnail
            })

    # Sort by season then designer
    collections.sort(key=lambda x: (x["season"], x["designer"]))
    return collections


def download_images_generator(season, designer):
    """Generator that yields SSE events for download progress"""
    import requests

    base_path = os.path.join(OUTPUT_DIR, season, designer)
    input_csv = os.path.join(base_path, "images.csv")
    output_folder = os.path.join(base_path, "images")

    if not os.path.exists(input_csv):
        yield f"data: {json.dumps({'type': 'error', 'message': 'No images.csv found. Extract links first.'})}\n\n"
        return

    categories = ["collection", "details", "beauty", "front-row"]
    os.makedirs(output_folder, exist_ok=True)

    # Group rows by category, deduplicating by ID
    categorized = {cat: [] for cat in categories}
    seen_ids = set()
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["id"] in seen_ids:
                continue
            seen_ids.add(row["id"])
            for cat in categories:
                if cat in row["url"]:
                    categorized[cat].append(row)
                    break

    # Count total and already downloaded
    total = sum(len(rows) for rows in categorized.values())
    if total == 0:
        yield f"data: {json.dumps({'type': 'error', 'message': 'No images found in CSV.'})}\n\n"
        return

    # Count already downloaded
    already_downloaded = 0
    for category, rows in categorized.items():
        cat_folder = os.path.join(output_folder, category)
        for row in rows:
            image_path = os.path.join(cat_folder, f"{row['id']}.jpg")
            if os.path.exists(image_path):
                already_downloaded += 1

    remaining = total - already_downloaded
    if remaining == 0:
        yield f"data: {json.dumps({'type': 'log', 'message': f'All {total} images already downloaded!'})}\n\n"
        yield f"data: {json.dumps({'type': 'progress', 'completed': total, 'total': total})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    yield f"data: {json.dumps({'type': 'log', 'message': f'{already_downloaded} already downloaded, {remaining} remaining...'})}\n\n"

    completed = 0

    for category, rows in categorized.items():
        if not rows:
            continue

        cat_folder = os.path.join(output_folder, category)
        os.makedirs(cat_folder, exist_ok=True)

        # Count how many need downloading in this category
        needs_download = sum(1 for row in rows if not os.path.exists(os.path.join(cat_folder, f"{row['id']}.jpg")))
        if needs_download > 0:
            yield f"data: {json.dumps({'type': 'log', 'message': f'Downloading {needs_download} {category} images...'})}\n\n"

        for row in rows:
            image_path = os.path.join(cat_folder, f"{row['id']}.jpg")

            # Skip if already downloaded
            if os.path.exists(image_path):
                completed += 1
                image_id = row["id"]
                msg = f"[{category}] Skipped (exists): {image_id}"
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed, 'total': total})}\n\n"
                continue

            try:
                response = requests.get(row["image_url"], stream=True, timeout=30)
                response.raise_for_status()

                with open(image_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)

                completed += 1
                image_id = row["id"]
                msg = f"[{category}] Downloaded: {image_id}"
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed, 'total': total})}\n\n"

            except Exception as e:
                completed += 1
                image_id = row["id"]
                msg = f"[{category}] Failed: {image_id} - {str(e)}"
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                yield f"data: {json.dumps({'type': 'progress', 'completed': completed, 'total': total})}\n\n"

    yield f"data: {json.dumps({'type': 'log', 'message': 'Download complete!'})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/collections")
def api_collections():
    return jsonify(get_collections())


@app.route("/api/seasons")
def api_seasons():
    """Get all available seasons, organized by year"""
    refresh = request.args.get('refresh', 'false').lower() == 'true'

    if not refresh:
        cached = load_seasons_cache()
        if cached:
            return jsonify(cached)

    # Fetch fresh from Vogue
    try:
        seasons_list = fetch_seasons_from_vogue()
        data = save_seasons_cache(seasons_list)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/designers/<season>")
def api_designers(season):
    """Get all designers for a season"""
    refresh = request.args.get('refresh', 'false').lower() == 'true'

    cache = load_designers_cache()

    if not refresh and season in cache:
        return jsonify({"season": season, "designers": cache[season]})

    # Fetch fresh from Vogue
    try:
        designers = fetch_designers_from_vogue(season)
        cache[season] = designers
        save_designers_cache(cache)
        return jsonify({"season": season, "designers": designers})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/extract", methods=["POST"])
def api_extract():
    data = request.json
    season = data.get("season", "").strip()
    designer = data.get("designer", "").strip()

    if not season or not designer:
        return jsonify({"error": "Season and designer are required"}), 400

    url = f"https://www.vogue.com/fashion-shows/{season}/{designer}/slideshow/collection#1"

    html = fetch_html(url)
    if not html:
        return jsonify({"error": f"Failed to fetch {url}"}), 500

    rows = extract_image_urls(html)
    if not rows:
        return jsonify({"error": "No images found on page"}), 404

    save_csv(rows, season, designer)

    # Count by category
    categories = {"collection": 0, "details": 0, "beauty": 0, "front-row": 0}
    for row in rows:
        for cat in categories:
            if cat in row["url"]:
                categories[cat] += 1
                break

    return jsonify({
        "success": True,
        "total": len(rows),
        "categories": categories,
        "season": season,
        "designer": designer
    })


@app.route("/api/download/<season>/<designer>")
def api_download(season, designer):
    return Response(
        download_images_generator(season, designer),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/api/missed/<season>/<designer>")
def api_missed(season, designer):
    """Get list of URLs that haven't been downloaded yet"""
    base_path = os.path.join(OUTPUT_DIR, season, designer)
    csv_path = os.path.join(base_path, "images.csv")
    images_path = os.path.join(base_path, "images")

    if not os.path.exists(csv_path):
        return jsonify({"error": "No images.csv found"}), 404

    # Get all downloaded image IDs
    downloaded_ids = set()
    if os.path.exists(images_path):
        for cat in os.listdir(images_path):
            cat_path = os.path.join(images_path, cat)
            if os.path.isdir(cat_path):
                for f in os.listdir(cat_path):
                    if f.endswith('.jpg'):
                        downloaded_ids.add(f.replace('.jpg', ''))

    # Find missed URLs (deduplicated by ID)
    missed = []
    seen_ids = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] not in downloaded_ids and row['id'] not in seen_ids:
                seen_ids.add(row['id'])
                missed.append({
                    'id': row['id'],
                    'url': row['url'],
                    'image_url': row['image_url']
                })

    return jsonify({
        "season": season,
        "designer": designer,
        "total_urls": len(downloaded_ids) + len(missed),
        "downloaded": len(downloaded_ids),
        "missed": missed
    })


@app.route("/images/<season>/<designer>/<category>/<filename>")
def serve_image(season, designer, category, filename):
    """Serve downloaded images"""
    image_dir = os.path.join(OUTPUT_DIR, season, designer, "images", category)
    return send_from_directory(image_dir, filename)


@app.route("/view/<season>/<designer>")
def view_collection(season, designer):
    """View all images in a collection"""
    images_path = os.path.join(OUTPUT_DIR, season, designer, "images")

    images_by_category = {}
    if os.path.exists(images_path):
        for cat in ["collection", "details", "beauty", "front-row"]:
            cat_path = os.path.join(images_path, cat)
            if os.path.isdir(cat_path):
                files = sorted([f for f in os.listdir(cat_path) if f.endswith('.jpg')])
                if files:
                    images_by_category[cat] = [f"/images/{season}/{designer}/{cat}/{f}" for f in files]

    return render_template("gallery.html",
                         season=season,
                         designer=designer,
                         images_by_category=images_by_category)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
