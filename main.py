import os
import json
from datetime import datetime
from face_verify import verify_face
from voice_verify import verify_voice

LOG_FILE = "access_log.txt"
DB_FILE = "database.json"

# -------------- OPTIONAL ARDUINO UNLOCK --------------
# import serial
# arduino = serial.Serial('COM4', 9600)

# --------------------------------------------------
# LOAD FACULTY INFO
# --------------------------------------------------
def get_faculty_info(faculty_id):
    if not os.path.exists(DB_FILE):
        return None, None

    with open(DB_FILE, "r") as f:
        db = json.load(f)

    info = db.get(str(faculty_id))
    if not info:
        return None, None

    return info.get("name", "UNKNOWN"), info.get("department", "UNKNOWN")

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
def log_access(faculty_id, method, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if faculty_id is None:
        log_entry = (
            f"{timestamp} | ID: UNKNOWN | Name: UNKNOWN | "
            f"Dept: UNKNOWN | Method: {method} | {status}\n"
        )
    else:
        name, department = get_faculty_info(faculty_id)
        log_entry = (
            f"{timestamp} | ID: {faculty_id} | Name: {name} | "
            f"Dept: {department} | Method: {method} | {status}\n"
        )

    with open(LOG_FILE, "a") as log:
        log.write(log_entry)

# --------------------------------------------------
# ACCESS CONTROL
# --------------------------------------------------
def unlock_door(faculty_id, method):
    name, department = get_faculty_info(faculty_id)

    print(f"\n🔓 ACCESS GRANTED")
    print(f"Faculty ID : {faculty_id}")
    print(f"Name       : {name}")
    print(f"Department : {department}")

    log_access(faculty_id, method, "GRANTED")

    # Arduino unlock (optional)
    # arduino.write(b"UNLOCK\n")

def deny_access(method):
    print("\n❌ ACCESS DENIED")
    log_access(None, method, "DENIED")

# --------------------------------------------------
# MAIN MENU
# --------------------------------------------------
def main():
    while True:
        print("\n====================================")
        print(" AI SMART CLASSROOM ACCESS SYSTEM ")
        print("====================================")
        print("[1] Facial Verification")
        print("[2] Voice Verification")
        print("[3] Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            print("\n🟦 Starting Facial Verification...")
            result = verify_face()

            if result:
                unlock_door(result, "FACE")
            else:
                deny_access("FACE")

        elif choice == "2":
            print("\n🟩 Starting Voice Verification...")
            result = verify_voice()

            if result:
                unlock_door(result, "VOICE")
            else:
                deny_access("VOICE")

        elif choice == "3":
            print("\nExiting system...")
            break

        else:
            print("\nInvalid choice. Try again.")

if __name__ == "__main__":
    main()
