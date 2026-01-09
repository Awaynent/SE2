import cv2
import os
import mediapipe as mp
import json

def register_face(faculty_id):
    folder = f"faces/{faculty_id}"
    os.makedirs(folder, exist_ok=True)

    mp_face = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)

    cam = cv2.VideoCapture(0)
    count = 0

    print("\nPlease look into the camera. Capturing 20 face samples...")

    while count < 20:
        ret, frame = cam.read()
        if not ret:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = mp_face.process(rgb)

        if result.multi_face_landmarks:
            file_path = f"{folder}/{count}.jpg"
            cv2.imwrite(file_path, frame)
            print(f"Captured face sample {count+1}/20")
            count += 1

        cv2.imshow("Face Registration", frame)
        if cv2.waitKey(1) == 27:
            break

    cam.release()
    cv2.destroyAllWindows()

    # ✅ DATABASE.JSON CREATION (RIGHT PLACE)
    db_file = "database.json"

    if os.path.exists(db_file):
        with open(db_file, "r") as f:
            db = json.load(f)
    else:
        db = {}

    db[str(faculty_id)] = {
        "face_path": f"faces/{faculty_id}",
        "voice_path": f"voices/{faculty_id}"
    }

    with open(db_file, "w") as f:
        json.dump(db, f, indent=4)

    print("Faculty registered and database updated.")
    return folder

if __name__ == "__main__":
    faculty_id = input("Enter Faculty ID: ")
    register_face(faculty_id)