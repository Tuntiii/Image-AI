import csv
from pathlib import Path
from flask import Flask, redirect, render_template, request, send_from_directory, url_for


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
LABELS_FILE = BASE_DIR / "labels.csv"
LABELS = ("dark", "vibrant", "minimal", "chaotic")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

app = Flask(__name__)


def get_images():
    if not IMAGE_DIR.exists():
        return []

    return sorted(
        [
            image.name
            for image in IMAGE_DIR.iterdir()
            if image.is_file() and image.suffix.lower() in IMAGE_EXTENSIONS
        ],
        key=str.lower,
    )


def get_label_map():
    if not LABELS_FILE.exists():
        return {}

    with LABELS_FILE.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {
            row["filename"]: row["label"]
            for row in reader
            if row.get("filename") and row.get("label")
        }


def save_label(filename, label):
    labels = get_label_map()
    labels[filename] = label

    with LABELS_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["filename", "label"])
        writer.writeheader()
        for image_name in get_images():
            if image_name in labels:
                writer.writerow({"filename": image_name, "label": labels[image_name]})


@app.route("/")
def index():
    images = get_images()
    labels = get_label_map()
    current_image = next((image for image in images if image not in labels), None)

    return render_template(
        "index.html",
        current_image=current_image,
        labels=LABELS,
        labeled_count=len(labels),
        total_count=len(images),
    )


@app.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(IMAGE_DIR, filename)


@app.route("/label", methods=["POST"])
def label_image():
    filename = request.form.get("filename")
    label = request.form.get("label")

    if filename and label in LABELS and (IMAGE_DIR / filename).exists():
        save_label(filename, label)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
