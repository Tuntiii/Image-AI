import argparse
import csv
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


DATASET_ZIP = Path("unsplash-research-dataset-lite-latest.zip")
PHOTO_TABLE = "photos.csv000"
IMAGE_DIR = Path("images")


def image_url(base_url, width, quality):
    parts = urllib.parse.urlsplit(base_url)
    query = dict(urllib.parse.parse_qsl(parts.query))
    query.update({"w": str(width), "q": str(quality), "fit": "max"})
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def download(url, output_path):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "local-unsplash-dataset-downloader/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        output_path.write_bytes(response.read())


def export_photos(dataset_zip, image_dir, limit, width, quality, delay, max_attempts):
    image_dir.mkdir(parents=True, exist_ok=True)
    attempted = 0
    downloaded = 0
    skipped = 0
    failed = 0

    with zipfile.ZipFile(dataset_zip) as archive:
        with archive.open(PHOTO_TABLE) as raw_file:
            text_file = (line.decode("utf-8") for line in raw_file)
            reader = csv.DictReader(text_file, delimiter="\t")

            for row in reader:
                photo_id = row["photo_id"]
                output_path = image_dir / f"unsplash-{photo_id}.jpg"

                if output_path.exists():
                    skipped += 1
                    continue

                url = image_url(row["photo_image_url"], width, quality)
                attempted += 1

                try:
                    download(url, output_path)
                except Exception as exc:
                    failed += 1
                    print(f"failed {photo_id}: {exc}")
                    if max_attempts and attempted >= max_attempts:
                        break
                    continue

                downloaded += 1
                print(f"downloaded {downloaded}: {output_path.name}")

                if limit and downloaded >= limit:
                    break

                if max_attempts and attempted >= max_attempts:
                    break

                if delay:
                    time.sleep(delay)

    return downloaded, skipped, failed


def main():
    parser = argparse.ArgumentParser(
        description="Download Unsplash Lite dataset photos into the local images folder."
    )
    parser.add_argument("--zip", type=Path, default=DATASET_ZIP)
    parser.add_argument("--output", type=Path, default=IMAGE_DIR)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--quality", type=int, default=80)
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=150,
        help="Stop after this many download attempts, even if some fail. Use 0 for no cap.",
    )
    args = parser.parse_args()

    downloaded, skipped, failed = export_photos(
        args.zip,
        args.output,
        args.limit,
        args.width,
        args.quality,
        args.delay,
        args.max_attempts,
    )
    output = str(args.output.resolve()).encode("ascii", "backslashreplace").decode("ascii")
    print(
        f"Done. Downloaded {downloaded}, skipped {skipped}, failed {failed}. "
        f"Saved in {output}"
    )


if __name__ == "__main__":
    main()
