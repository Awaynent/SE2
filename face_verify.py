import cv2
import json
import os
import numpy as np
import mediapipe as mp
import time

# =============================
# LIVENESS CONFIG
# =============================
EAR_THRESHOLD = 0.18        # eye closed threshold
BLINK_FRAMES = 2            # frames eyes must stay closed
REQUIRED_BLINKS = 2         # number of blinks required

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

# =============================
# MAIN VERIFICATION FUNCTION
# =============================
def verify_face():

    # --- Load trained model ---
    if not os.path.exists("face_model.yml"):
        print("❌ Face model not found. Train first.")
        return None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("face_model.yml")

    # --- Load database ---
    if not os.path.exists("database.json"):
        print("❌ database.json not found.")
        return None

    db = json.load(open("database.json", "r"))

    # --- Face detector ---
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # --- MediaPipe Face Mesh ---
    mp_face = mp.solutions.face_mesh
    mesh = mp_face.FaceMesh(refine_landmarks=True)

    cap = cv2.VideoCapture(0)

    blink_count = 0
    eye_closed_frames = 0

    print("🟦 Face verification started")
    print("👁️ Please BLINK twice to confirm liveness")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        results = mesh.process(rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            left_eye = np.array([[landmarks[i].x, landmarks[i].y] for i in LEFT_EYE])
            right_eye = np.array([[landmarks[i].x, landmarks[i].y] for i in RIGHT_EYE])

            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2

            if ear < EAR_THRESHOLD:
                eye_closed_frames += 1
            else:
                if eye_closed_frames >= BLINK_FRAMES:
                    blink_count += 1
                    print(f"👁️ Blink detected ({blink_count}/{REQUIRED_BLINKS})")
                eye_closed_frames = 0

        # Draw face box & attempt recognition ONLY if live
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]

            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            cv2.putText(
                frame,
                f"Blinks: {blink_count}/{REQUIRED_BLINKS}",
                (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0,255,0),
                2
            )

            if blink_count >= REQUIRED_BLINKS:
                try:
                    id_, confidence = recognizer.predict(face_img)
                except:
                    continue

                if confidence < 60:
                    faculty_id = str(id_)
                    print(f"✅ Access Granted: Faculty ID {faculty_id}")
                    cap.release()
                    cv2.destroyAllWindows()
                    return faculty_id

        cv2.imshow("Face Verification", frame)

        if cv2.waitKey(1) == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    print("❌ Face verification failed.")
    return None
