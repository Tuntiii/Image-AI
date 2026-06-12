import csv
from pathlib import Path
from flask import Flask, redirect, render_template, request, send_from_directory, url_for


project_dir = Path(__file__).resolve().parent
images_folder = project_dir / "images"
labels_csv = project_dir / "labels.csv"
skipped_csv = project_dir / "skipped.csv"
label_choices = ("dark", "vibrant", "minimal", "chaotic")
image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

app = Flask(__name__)


def get_images():
    if not images_folder.exists():
        return []

    return sorted(
        [
            image.name
            for image in images_folder.iterdir()
            if image.is_file() and image.suffix.lower() in image_extensions
        ],
        key=str.lower,
    )


def get_label_map():
    if not labels_csv.exists():
        return {}

    with labels_csv.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {
            row["filename"]: row["label"]
            for row in reader
            if row.get("filename") and row.get("label")
        }


def get_skipped_images():
    if not skipped_csv.exists():
        return set()

    with skipped_csv.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return {row["filename"] for row in reader if row.get("filename")}


def save_label(filename, label):
    labels = get_label_map()
    labels[filename] = label

    with labels_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["filename", "label"])
        writer.writeheader()
        for image_name in get_images():
            if image_name in labels:
                writer.writerow({"filename": image_name, "label": labels[image_name]})


def save_skip(filename):
    skipped = get_skipped_images()
    skipped.add(filename)

    with skipped_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["filename"])
        writer.writeheader()
        for image_name in get_images():
            if image_name in skipped:
                writer.writerow({"filename": image_name})


@app.route("/")
def index():
    images = get_images()
    labels = get_label_map()
    skipped = get_skipped_images()
    current_image = next(
        (image for image in images if image not in labels and image not in skipped),
        None,
    )

    return render_template(
        "index.html",
        current_image=current_image,
        labels=label_choices,
        labeled_count=len(labels),
        skipped_count=len(skipped),
        total_count=len(images),
    )


@app.route("/images/<path:filename>")
def image_file(filename):
    return send_from_directory(images_folder, filename)


@app.route("/label", methods=["POST"])
def label_image():
    filename = request.form.get("filename")
    label = request.form.get("label")

    if filename and label in label_choices and (images_folder / filename).exists():
        save_label(filename, label)

    return redirect(url_for("index"))


@app.route("/skip", methods=["POST"])
def skip_image():
    filename = request.form.get("filename")

    if filename and (images_folder / filename).exists():
        save_skip(filename)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
