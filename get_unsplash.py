import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

import requests


API_URL = "https://api.unsplash.com/search/photos"
project_dir = Path(__file__).resolve().parent
images_folder = project_dir / "images"


def require_access_key():
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise SystemExit(
            "Missing UNSPLASH_ACCESS_KEY.\n"
            "Create a free Unsplash developer app, copy its Access Key, then run:\n"
            '$env:UNSPLASH_ACCESS_KEY="paste_your_access_key_here"'
        )
    return access_key


def sized_image_url(url, width, quality):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query.update({"w": str(width), "q": str(quality), "fit": "max"})
    return urlunsplit(parts._replace(query=urlencode(query)))


def filename_prefix(query):
    prefix = re.sub(r"[^a-zA-Z0-9_-]+", "-", query.strip().lower()).strip("-")
    return prefix or "unsplash"


def console_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def search_photos(query, count, access_key, per_page):
    photos = []
    page = 1

    while len(photos) < count:
        response = requests.get(
            API_URL,
            headers={"Authorization": f"Client-ID {access_key}"},
            params={
                "query": query,
                "page": page,
                "per_page": min(per_page, count - len(photos)),
                "content_filter": "high",
                "order_by": "relevant",
            },
            timeout=30,
        )

        if response.status_code == 403:
            raise SystemExit("Unsplash rejected the request. Check your access key or rate limit.")

        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])

        if not results:
            break

        photos.extend(results)
        page += 1

    return photos[:count]


def download_photo(photo, output_dir, query, width, quality, access_key):
    photo_id = photo["id"]
    photographer = photo["user"]["username"]
    image_url = sized_image_url(photo["urls"]["raw"], width, quality)
    output_path = output_dir / f"{filename_prefix(query)}-{photo_id}.jpg"

    if output_path.exists():
        return output_path, "skipped"

    response = requests.get(image_url, timeout=30)
    response.raise_for_status()
    output_path.write_bytes(response.content)

    download_location = photo.get("links", {}).get("download_location")
    if download_location:
        requests.get(
            download_location,
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=30,
        )

    return output_path, f"saved by {photographer}"


def main():
    parser = argparse.ArgumentParser(description="Download photos from the official Unsplash API.")
    parser.add_argument("query", nargs="?", default="vibrant")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--output", type=Path, default=images_folder)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--quality", type=int, default=80)
    parser.add_argument("--per-page", type=int, default=30)
    args = parser.parse_args()

    access_key = require_access_key()
    args.output.mkdir(parents=True, exist_ok=True)

    photos = search_photos(args.query, args.count, access_key, args.per_page)
    if not photos:
        raise SystemExit(f"No Unsplash photos found for {args.query!r}.")

    for index, photo in enumerate(photos, start=1):
        output_path, status = download_photo(
            photo,
            args.output,
            args.query,
            args.width,
            args.quality,
            access_key,
        )
        print(f"{index:03}: {console_text(output_path)} ({status})")

    print(f"Done. {len(photos)} photos for {args.query!r} are in {console_text(args.output)}.")


if __name__ == "__main__":
    main()
