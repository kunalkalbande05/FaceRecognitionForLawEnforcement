# SentinelSight – Real-Time Face Recognition System

SentinelSight is a real-time facial recognition web application designed for monitoring and managing individuals of interest. Built with Python, Flask, OpenCV, and SQLite, the system allows law enforcement officers to add, recognize, and track faces using live camera feeds.

Note: This project is built for academic purposes. While the methodology is inspired by LBPH and ArcFace concepts, the implementation uses a simplified face recognition pipeline based on Haar cascades and custom feature embeddings.

---

## Table of Contents
- Features
- System Overview
- Workflow
- Setup & Installation
- Usage
- Folder Structure
- Technologies Used
- Future Improvements
- License

---

## Features
- Real-time face detection and recognition using a webcam
- Add new individuals (criminals) with associated metadata
- Dashboard to view registered individuals and live recognition results
- Confidence-based alerts for recognized faces
- Dummy statistics and alerts API for simulation
- Human-in-the-loop verification via web interface
- Lightweight model storage using pickle

---

## System Overview
The project draws inspiration from academic facial recognition methods combining:

- LBPH (Local Binary Pattern Histogram) – classical texture-based recognition
- ArcFace (Deep CNN with additive angular margin) – modern embedding-based recognition

Actual Implementation:
- Face detection: Haar cascade classifier
- Feature encoding: custom flattened grayscale face arrays
- Matching: cosine similarity between stored and live embeddings
- Storage: SQLite database + pickle file for face encodings

The system allows human verification before any enforcement action, simulating ethical and legal safeguards.

---

## Workflow
1. **Data Acquisition**
   - Upload images of individuals to the system (criminals database)
   - Webcam feed captures live faces

2. **Preprocessing & Feature Extraction**
   - Detect faces using Haar cascades
   - Crop, resize, and normalize images
   - Flatten face region into a 1D feature vector (0–1 scaled)

3. **Face Matching**
   - Compute cosine similarity between live face and stored encodings
   - If similarity > 60%, consider as a potential match

4. **Human Verification**
   - Matches are reviewed in the dashboard
   - Only manually confirmed matches are flagged

---

## Setup & Installation

1. Clone the repository
2. Create a virtual environment 
3. Install dependencies
4. Run the application
5. Open your browser and go to: http://localhost:5000
6. Default login for testing:
- Badge ID: BDG123
- Password: password123

---

## Usage
- Upload images of individuals via `/api/criminals`
- Start live camera scanning via the dashboard
- Recognized faces appear with confidence percentage
- Manual verification ensures safe identification

---

## Folder Structure
```text
SentinelSight/
app.py # Main Flask application
requirements.txt # Python dependencies
sentinel.db # SQLite database
models/
face_encodings.pkl # Stored face embeddings
static/
uploads/
criminals/ # Uploaded images
templates/ # HTML templates
README.md # Project documentation
```


---

## Technologies Used
- Python 3.10+
- Flask (Web Framework)
- OpenCV (Face detection & image processing)
- SQLite (Database)
- SocketIO (Real-time alerts)
- Pickle (Model storage)

---

## Future Improvements
- Integrate deep learning models like ArcFace for higher accuracy
- Implement LBPH module for resource-constrained environments
- Improve UI/UX of dashboard
- Add secure authentication and role-based access
- Expand dataset with anonymized images for testing
- Add logging & audit trail for alerts

---

## License
This project is for educational purposes only. Do not use it for real-world surveillance or law enforcement applications.

SentinelSight | 2025
