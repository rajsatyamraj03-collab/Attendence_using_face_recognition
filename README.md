# 🎓 EduFace — Student Attendance System with Face Recognition

A full-stack attendance management system using **real-time face recognition** via webcam.

## 📁 Project Structure

```
attendance_system/
├── app.py                # Flask backend (API server)
├── index.html            # Frontend (beautiful dark UI)
├── requirements.txt      # Python dependencies
├── students.json         # Student database (auto-created)
├── student_faces/        # Stored face images & encodings
└── attendance_logs/      # Daily attendance JSON logs
```

---

## ⚙️ Installation

### Step 1: Install Python dependencies

```bash
# Basic (demo mode - no real face recognition)
pip install flask flask-cors numpy Pillow

# Full face recognition (recommended)
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y cmake libboost-all-dev libopenblas-dev

pip install dlib
pip install face-recognition
pip install flask flask-cors numpy Pillow
```

### Step 2: Run the server

```bash
cd attendance_system
python app.py
```

### Step 3: Open the app

Open `index.html` in your browser **or** visit `http://localhost:5000`

---

## 🚀 Features

| Feature | Description |
|--------|-------------|
| 📸 Face Registration | Capture student face via webcam and store encoding |
| 🔍 Auto Face Scan | Continuous webcam scanning marks attendance automatically |
| ✅ Manual Override | Mark students present/absent manually from the report |
| 📊 Daily Reports | View present/absent counts with timestamps |
| 📅 History | Browse past attendance records by date |
| ⬇️ CSV Export | Download today's attendance as a spreadsheet |
| 🔒 Offline | Works fully offline — no cloud dependency |

---

## 🔧 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/status` | System status & face recognition availability |
| GET | `/api/students` | List all students with today's status |
| POST | `/api/students` | Register new student with photo |
| DELETE | `/api/students/<id>` | Remove a student |
| POST | `/api/recognize` | Scan a face and mark attendance |
| GET | `/api/attendance/today` | Today's attendance report |
| GET | `/api/attendance/history` | Past 30 days summary |
| POST | `/api/attendance/manual` | Manually toggle a student's attendance |
| GET | `/api/attendance/export` | Download CSV |

---

## 📱 How to Use

### Register a Student
1. Go to **Register Student** tab
2. Enter name, roll number, class
3. Click **Start Camera**, face the webcam
4. Click **Capture Photo**
5. Click **Register Student**

### Mark Attendance
1. Go to **Mark Attendance** tab
2. Click **Start Camera**
3. Student faces the camera
4. Click **Scan Face** OR enable **Auto Scan** (scans every 3 seconds)
5. Attendance is marked with timestamp

### View Reports
- **Today's Report** — full list with present/absent status
- **History** — past attendance summaries
- **Export CSV** — download for Excel

---

## 🛠 Requirements

- Python 3.8+
- Webcam
- Modern browser (Chrome, Firefox, Edge)
- For face recognition: CMake, dlib (see install steps above)

---

## ⚠️ Demo Mode

If `face_recognition` is not installed, the system runs in **demo mode**:
- All other features work normally
- Face scanning marks the first registered student (for testing)
- Install `face-recognition` for real recognition

---

## 🔒 Privacy Note

All face data is stored **locally on your machine**. No data is sent to any server.
