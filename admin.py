import os
import json
import shutil

from face_capture import capture as face_capture
from face_train import train as face_train
from voice_capture import capture as voice_capture

DATABASE_FILE = "database.json"
FACE_DIR = "faces"
VOICE_DIR = "voices"
FACE_MODEL = "face_model.yml"

# ---------------- DATABASE ----------------
def load_db():
    if not os.path.exists(DATABASE_FILE):
        return {}

    with open(DATABASE_FILE, "r") as f:
        db = json.load(f)

    # ---- AUTO-FIX OLD / BROKEN ENTRIES ----
    fixed_db = {}
    new_id = 1

    for key, value in db.items():
        if key.isdigit():
            fixed_db[key] = value
        else:
            fixed_db[str(new_id)] = {
                "name": key,
                "department": value.get("department", "Unknown"),
                "face_path": value.get("face_path", f"{FACE_DIR}/{new_id}"),
                "voice_path": value.get("voice_path", f"{VOICE_DIR}/{new_id}")
            }
            new_id += 1

    if fixed_db != db:
        save_db(fixed_db)

    return fixed_db

def save_db(db):
    with open(DATABASE_FILE, "w") as f:
        json.dump(db, f, indent=4)

def generate_faculty_id(db):
    numeric_ids = [int(fid) for fid in db.keys() if fid.isdigit()]
    return str(max(numeric_ids) + 1) if numeric_ids else "1"

# ---------------- ADMIN ACTIONS ----------------
def add_faculty():
    db = load_db()

    print("\n--- ADD FACULTY ---")
    print("Type 'B' anytime to cancel\n")

    name = input("Enter faculty name: ").strip()
    if name.lower() in ["b", "0"]:
        print("↩️ Returning to admin menu.")
        return

    department = input("Enter department: ").strip()
    if department.lower() in ["b", "0"]:
        print("↩️ Returning to admin menu.")
        return

    faculty_id = generate_faculty_id(db)
    print(f"\n🆔 Assigned Faculty ID: {faculty_id}")

    confirm = input("Proceed with enrollment? (Y/N): ").strip().lower()
    if confirm != "y":
        print("❌ Enrollment cancelled.")
        return

    # ---------- FACE ----------
    print("\n[1/3] Capturing FACE samples (30 images)...")
    face_capture(faculty_id)

    print("\n[2/3] Training face recognition model...")
    face_train()

    # ---------- VOICE ----------
    print("\n[3/3] Capturing VOICE samples (5 recordings × 3s)...")
    voice_capture(faculty_id)

    # ---------- SAVE ----------
    db[faculty_id] = {
        "name": name,
        "department": department,
        "face_path": f"{FACE_DIR}/{faculty_id}",
        "voice_path": f"{VOICE_DIR}/{faculty_id}"
    }

    save_db(db)
    print(f"\n✅ Faculty '{name}' enrolled successfully!")

def delete_faculty():
    db = load_db()
    if not db:
        print("❌ No faculty registered.")
        return

    print("\n--- DELETE FACULTY ---")
    print("Type 'B' or '0' to cancel\n")

    print("Registered Faculty:")
    for fid, info in db.items():
        print(f"ID {fid}: {info.get('name', 'UNKNOWN')}")

    fid = input("\nEnter Faculty ID to delete: ").strip()
    if fid.lower() in ["b", "0"]:
        print("↩️ Deletion cancelled.")
        return

    if fid not in db:
        print("❌ Invalid Faculty ID.")
        return

    confirm = input(
        f"Are you sure you want to delete '{db[fid]['name']}'? (Y/N): "
    ).strip().lower()

    if confirm != "y":
        print("❌ Deletion cancelled.")
        return

    # ---------- DELETE DATA ----------
    shutil.rmtree(os.path.join(FACE_DIR, fid), ignore_errors=True)
    shutil.rmtree(os.path.join(VOICE_DIR, fid), ignore_errors=True)

    del db[fid]
    save_db(db)

    # ---------- RETRAIN FACE MODEL ----------
    if os.path.exists(FACE_DIR) and os.listdir(FACE_DIR):
        print("\n🔄 Retraining face model...")
        face_train()
    else:
        if os.path.exists(FACE_MODEL):
            os.remove(FACE_MODEL)
            print("⚠️ No faces left. Face model removed.")

    print("✅ Faculty deleted successfully.")

# ---------------- MENU ----------------
def menu():
    while True:
        print("\n====== ADMIN PANEL ======")
        print("[1] Add Faculty")
        print("[2] Delete Faculty")
        print("[3] Exit")

        choice = input("Select option: ").strip()

        if choice == "1":
            add_faculty()
        elif choice == "2":
            delete_faculty()
        elif choice == "3":
            print("Exiting admin panel.")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    menu()
