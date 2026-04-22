"""
Student Attendance System with Face Recognition
Backend: Flask + face_recognition + OpenCV
"""

import os
import json
import base64
import io
import csv
import logging
from datetime import datetime, date
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from PIL import Image
import numpy as np

# Try to import face_recognition (optional - graceful fallback)
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("⚠️  face_recognition not installed. Using demo mode.")

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ─── Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
FACES_DIR = BASE_DIR / "student_faces"
LOGS_DIR  = BASE_DIR / "attendance_logs"
DB_FILE   = BASE_DIR / "students.json"

FACES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── In-memory student DB ────────────────────────────────
def load_students():
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            return json.load(f)
    return {}

def save_students(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

students_db = load_students()

# ─── Helpers ─────────────────────────────────────────────
def base64_to_image(b64_string):
    """Convert base64 image string to PIL Image."""
    if "," in b64_string:
        b64_string = b64_string.split(",")[1]
    img_bytes = base64.b64decode(b64_string)
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")

def image_to_numpy(pil_image):
    return np.array(pil_image)

def get_face_encoding(pil_image):
    """Get 128-d face encoding from PIL image."""
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    img_np = image_to_numpy(pil_image)
    encodings = face_recognition.face_encodings(img_np)
    return encodings[0].tolist() if encodings else None

def load_all_encodings():
    """Load all known face encodings from disk."""
    known_encodings = []
    known_ids = []
    for sid, info in students_db.items():
        enc_path = FACES_DIR / f"{sid}_encoding.json"
        if enc_path.exists():
            with open(enc_path) as f:
                encoding = json.load(f)
            known_encodings.append(encoding)
            known_ids.append(sid)
    return known_encodings, known_ids

def today_log_path():
    return LOGS_DIR / f"{date.today().isoformat()}.json"

def load_today_attendance():
    path = today_log_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}

def save_today_attendance(data):
    with open(today_log_path(), "w") as f:
        json.dump(data, f, indent=2)

# ─── Routes ──────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/api/status")
def status():
    return jsonify({
        "face_recognition": FACE_RECOGNITION_AVAILABLE,
        "student_count": len(students_db),
        "demo_mode": not FACE_RECOGNITION_AVAILABLE
    })

@app.route("/api/students", methods=["GET"])
def get_students():
    today = load_today_attendance()
    result = []
    for sid, info in students_db.items():
        result.append({
            "id": sid,
            "name": info["name"],
            "roll": info.get("roll", ""),
            "class": info.get("class", ""),
            "photo": info.get("photo_b64", ""),
            "present_today": sid in today,
            "time_marked": today.get(sid, {}).get("time", "")
        })
    return jsonify(result)

@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.json
    name  = data.get("name", "").strip()
    roll  = data.get("roll", "").strip()
    cls   = data.get("class", "").strip()
    photo = data.get("photo", "")

    if not name or not photo:
        return jsonify({"error": "Name and photo required"}), 400

    # Generate student ID
    sid = f"STU{len(students_db)+1:04d}"

    # Process image
    try:
        pil_img = base64_to_image(photo)
        pil_img = pil_img.resize((300, 300))
    except Exception as e:
        return jsonify({"error": f"Invalid image: {e}"}), 400

    # Get face encoding
    encoding = get_face_encoding(pil_img)
    if FACE_RECOGNITION_AVAILABLE and encoding is None:
        return jsonify({"error": "No face detected in the image. Please retake."}), 400

    # Save encoding
    enc_path = FACES_DIR / f"{sid}_encoding.json"
    with open(enc_path, "w") as f:
        json.dump(encoding if encoding else [], f)

    # Save thumbnail as base64
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=70)
    thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    # Save face image to disk
    img_path = FACES_DIR / f"{sid}.jpg"
    pil_img.save(img_path, "JPEG")

    # Store in DB
    students_db[sid] = {
        "name": name,
        "roll": roll,
        "class": cls,
        "photo_b64": thumb_b64,
        "registered_at": datetime.now().isoformat()
    }
    save_students(students_db)

    return jsonify({"success": True, "id": sid, "name": name})

@app.route("/api/students/<sid>", methods=["DELETE"])
def delete_student(sid):
    if sid not in students_db:
        return jsonify({"error": "Student not found"}), 404
    del students_db[sid]
    save_students(students_db)
    # Remove face files
    for ext in ["_encoding.json", ".jpg"]:
        p = FACES_DIR / f"{sid}{ext}"
        if p.exists():
            p.unlink()
    return jsonify({"success": True})

@app.route("/api/recognize", methods=["POST"])
def recognize():
    data = request.json
    photo = data.get("photo", "")

    if not photo:
        return jsonify({"error": "No photo provided"}), 400

    try:
        pil_img = base64_to_image(photo)
    except Exception as e:
        return jsonify({"error": f"Invalid image: {e}"}), 400

    if not FACE_RECOGNITION_AVAILABLE:
        # Demo mode: randomly mark a student present for testing
        if students_db:
            sid = list(students_db.keys())[0]
            today = load_today_attendance()
            if sid not in today:
                today[sid] = {"time": datetime.now().strftime("%H:%M:%S"), "date": date.today().isoformat()}
                save_today_attendance(today)
            info = students_db[sid]
            return jsonify({
                "match": True,
                "demo_mode": True,
                "student": {"id": sid, "name": info["name"], "roll": info.get("roll",""), "class": info.get("class","")},
                "time": today[sid]["time"]
            })
        return jsonify({"match": False, "message": "No students registered"})

    # Real face recognition
    img_np = image_to_numpy(pil_img)
    unknown_encodings = face_recognition.face_encodings(img_np)

    if not unknown_encodings:
        return jsonify({"match": False, "message": "No face detected in frame"})

    known_encodings, known_ids = load_all_encodings()
    if not known_encodings:
        return jsonify({"match": False, "message": "No students registered yet"})

    known_np = [np.array(e) for e in known_encodings]

    # Check each detected face
    for unknown_enc in unknown_encodings:
        distances = face_recognition.face_distance(known_np, unknown_enc)
        best_idx  = int(np.argmin(distances))
        best_dist = float(distances[best_idx])

        if best_dist < 0.5:  # threshold
            sid = known_ids[best_idx]
            info = students_db[sid]
            today = load_today_attendance()
            already = sid in today
            if not already:
                today[sid] = {"time": datetime.now().strftime("%H:%M:%S"), "date": date.today().isoformat()}
                save_today_attendance(today)
            return jsonify({
                "match": True,
                "already_marked": already,
                "confidence": round((1 - best_dist) * 100, 1),
                "student": {"id": sid, "name": info["name"], "roll": info.get("roll",""), "class": info.get("class","")},
                "time": today[sid]["time"]
            })

    return jsonify({"match": False, "message": "Face not recognized"})

@app.route("/api/attendance/today", methods=["GET"])
def attendance_today():
    today = load_today_attendance()
    total = len(students_db)
    present_ids = set(today.keys())
    result = []
    for sid, info in students_db.items():
        result.append({
            "id": sid,
            "name": info["name"],
            "roll": info.get("roll",""),
            "class": info.get("class",""),
            "present": sid in present_ids,
            "time": today.get(sid, {}).get("time","—")
        })
    return jsonify({
        "date": date.today().isoformat(),
        "total": total,
        "present": len(present_ids),
        "absent": total - len(present_ids),
        "records": result
    })

@app.route("/api/attendance/history", methods=["GET"])
def attendance_history():
    logs = []
    for log_file in sorted(LOGS_DIR.glob("*.json"), reverse=True)[:30]:
        log_date = log_file.stem
        with open(log_file) as f:
            data = json.load(f)
        logs.append({
            "date": log_date,
            "present": len(data),
            "total": len(students_db)
        })
    return jsonify(logs)

@app.route("/api/attendance/manual", methods=["POST"])
def manual_attendance():
    data = request.json
    sid = data.get("student_id")
    present = data.get("present", True)
    if sid not in students_db:
        return jsonify({"error": "Student not found"}), 404
    today = load_today_attendance()
    if present:
        today[sid] = {"time": datetime.now().strftime("%H:%M:%S"), "date": date.today().isoformat(), "manual": True}
    else:
        today.pop(sid, None)
    save_today_attendance(today)
    return jsonify({"success": True})

@app.route("/api/attendance/export", methods=["GET"])
def export_csv():
    today = load_today_attendance()
    rows = [["Student ID","Name","Roll","Class","Status","Time"]]
    for sid, info in students_db.items():
        rows.append([
            sid, info["name"], info.get("roll",""), info.get("class",""),
            "Present" if sid in today else "Absent",
            today.get(sid, {}).get("time","—")
        ])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    csv_data = output.getvalue()
    from flask import Response
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename=attendance_{date.today()}.csv"})

if __name__ == "__main__":
    print("🎓 Student Attendance System starting...")
    print(f"   Face Recognition: {'✅ Available' if FACE_RECOGNITION_AVAILABLE else '⚠️  Demo Mode (install face_recognition)'}")
    print(f"   Open: http://localhost:5000")
    app.run(debug=True, port=5000)
