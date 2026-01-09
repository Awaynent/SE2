import cv2
import os
import numpy as np

def train():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faces = []
    labels = []
    label = 0

    for faculty_id in os.listdir("faces/"):
        folder = f"faces/{faculty_id}"

        for img in os.listdir(folder):
            img_path = f"{folder}/{img}"
            gray = cv2.imread(img_path, 0)

            faces.append(gray)
            labels.append(int(faculty_id))

        label += 1

    recognizer.train(faces, np.array(labels))
    recognizer.write("face_model.yml")
    print("Training complete! Model saved as face_model.yml")

if __name__ == "__main__":
    train()