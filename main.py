import cv2
import numpy as np
from pathlib import Path
import csv
from sklearn.neighbors import KNeighborsClassifier
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score

IMAGE_DIR = Path("images")
LABELS_FILE = Path("labels.csv")

def extract_features(image_path):
    img = cv2.imread(image_path)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([img_hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
    return hist.flatten() / hist.sum() 

X = []
y = []
filenames = []

with LABELS_FILE.open("r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        filename = row["filename"]
        label = row["label"]

        image_path = IMAGE_DIR / filename

        features = extract_features(str(image_path))

        X.append(features)
        y.append(label)
        filenames.append(filename)

X = np.array(X)
y = np.array(y)

print("Training data:", X.shape)
print("Labels:", y.shape)

model = KNeighborsClassifier(n_neighbors=3)

scores = cross_val_score(model, X, y, cv=5)
print(scores)
model.fit(X, y)

test_image = Path("charlesdeluvio-pcZvxrAyYoQ-unsplash.jpg")
test_features = extract_features(str(test_image))
test_features = test_features.reshape(1, -1)

predicted_label = model.predict(test_features)[0]

print("Predicted label:", predicted_label)


    



