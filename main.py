import csv
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn
from torchvision import models


image_dir = Path("images")
labels_file = Path("labels.csv")
test_image = Path("managing-chaos-managing-chaos-as-business-concept-businessman-navigating-confusing-tangled-network-ropes-423839572.webp")
batch_size = 16


def load_labels(labels_file, image_dir):
    image_paths = []
    labels = []

    with labels_file.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            image_path = image_dir / row["filename"]
            if not image_path.exists():
                print(f"Skipping missing image: {image_path}")
                continue

            image_paths.append(image_path)
            labels.append(row["label"])

    if not image_paths:
        raise SystemExit(f"No labeled images found from {labels_file}.")

    return image_paths, np.array(labels)


def build_cnn_embedder(device):
    cache_dir = Path(".torch_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    torch.hub.set_dir(str(cache_dir))

    weights = models.ResNet18_Weights.DEFAULT
    model = models.resnet18(weights=weights)
    model.fc = nn.Identity()
    model.eval()
    model.to(device)
    return model, weights.transforms()


def load_image(image_path, preprocess):
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        return preprocess(image)


def extract_embeddings(image_paths, batch_size=16):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, preprocess = build_cnn_embedder(device)
    embeddings = []

    with torch.inference_mode():
        for start in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[start : start + batch_size]
            batch = torch.stack([load_image(path, preprocess) for path in batch_paths]).to(device)
            batch_embeddings = model(batch).cpu().numpy()
            embeddings.append(batch_embeddings)

    embeddings = np.vstack(embeddings).astype(np.float32)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings / np.maximum(norms, 1e-12)


def predict_image(model, image_path, batch_size):
    if not image_path.exists():
        raise SystemExit(f"Test image not found: {image_path}")

    embedding = extract_embeddings([image_path], batch_size=batch_size)
    prediction = model.predict(embedding)[0]

    print(f"Prediction: {prediction}")

    if hasattr(model[-1], "predict_proba"):
        probabilities = model.predict_proba(embedding)[0]
        ranked = sorted(zip(model[-1].classes_, probabilities), key=lambda item: item[1], reverse=True)
        for label, probability in ranked:
            print(f"{label}: {probability:.3f}")


def main():
    image_paths, labels = load_labels(labels_file, image_dir)
    X = extract_embeddings(image_paths, batch_size=batch_size)

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
    )
    model.fit(X, labels)

    predict_image(model, test_image, batch_size=batch_size)


if __name__ == "__main__":
    main()
