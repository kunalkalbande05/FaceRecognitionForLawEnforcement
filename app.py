
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import os
import sqlite3
from datetime import datetime
import threading
import time
import logging
from werkzeug.utils import secure_filename
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.secret_key = 'sentinel-sight-secret-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads/criminals'
app.config['MODEL_FOLDER'] = 'models'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables
camera = None
scanning_active = False
camera_lock = threading.Lock()

class FaceRecognition:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.load_model()
    
    def extract_face_encoding(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return None
            
            x, y, w, h = faces[0]
            face_roi = gray[y:y+h, x:x+w]
            face_standard = cv2.resize(face_roi, (100, 100))
            face_encoding = face_standard.flatten()
            face_encoding = face_encoding / 255.0
            
            return face_encoding
        except Exception as e:
            logger.error(f"Face extraction error: {e}")
            return None
    
    def compare_faces(self, encoding1, encoding2):
        try:
            if encoding1 is None or encoding2 is None:
                return 0.0
            return np.dot(encoding1, encoding2) / (np.linalg.norm(encoding1) * np.linalg.norm(encoding2))
        except:
            return 0.0
    
    def load_model(self):
        try:
            model_path = os.path.join(app.config['MODEL_FOLDER'], 'face_encodings.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                    self.known_face_ids = data.get('ids', [])
                logger.info(f"✅ Loaded {len(self.known_face_encodings)} face encodings")
        except Exception as e:
            logger.error(f"Model load error: {e}")
    
    def save_model(self):
        try:
            model_path = os.path.join(app.config['MODEL_FOLDER'], 'face_encodings.pkl')
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'ids': self.known_face_ids
            }
            with open(model_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Model save error: {e}")
    
    def add_criminal_face(self, criminal_id, name, image_path):
        try:
            face_encoding = self.extract_face_encoding(image_path)
            if face_encoding is None:
                return False
            
            
            if criminal_id in self.known_face_ids:
                idx = self.known_face_ids.index(criminal_id)
                self.known_face_encodings[idx] = face_encoding
                self.known_face_names[idx] = name
            else:
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                self.known_face_ids.append(criminal_id)
            
            self.save_model()
            logger.info(f"✅ Added face for {name}")
            return True
        except Exception as e:
            logger.error(f"Add criminal error: {e}")
            return False
    
    def recognize_faces(self, frame):
        try:
            # Fix camera orientation
            frame = cv2.flip(frame, 1)  
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            results = []
            
            for (x, y, w, h) in faces:
                try:
                    face_roi = gray[y:y+h, x:x+w]
                    face_standard = cv2.resize(face_roi, (100, 100))
                    live_encoding = face_standard.flatten() / 255.0
                    
                    best_match = -1
                    best_score = 0.0
                    
                    for i, stored_encoding in enumerate(self.known_face_encodings):
                        score = self.compare_faces(live_encoding, stored_encoding)
                        if score > best_score:
                            best_score = score
                            best_match = i
                    
                    confidence = best_score * 100
                    if best_match != -1 and confidence > 60:
                        results.append({
                            'criminal_id': self.known_face_ids[best_match],
                            'name': self.known_face_names[best_match],
                            'confidence': round(confidence, 2),
                            'location': (x, y, w, h)
                        })
                        logger.info(f"🔍 Match: {self.known_face_names[best_match]} ({confidence}%)")
                        
                except Exception as e:
                    continue
            
            return results
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return []

face_system = FaceRecognition()

def init_db():
    """Initialize database"""
    try:
        conn = sqlite3.connect('sentinel.db')
        c = conn.cursor()
        
        # Create tables
        c.execute('''
            CREATE TABLE IF NOT EXISTS officers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id TEXT UNIQUE,
                name TEXT,
                email TEXT,
                password TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS criminals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criminal_id TEXT UNIQUE,
                name TEXT,
                image_path TEXT,
                offenses TEXT,
                risk_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default officer
        c.execute("SELECT COUNT(*) FROM officers WHERE badge_id = 'BDG123'")
        if c.fetchone()[0] == 0:
            c.execute('''
                INSERT INTO officers (badge_id, name, email, password, department)
                VALUES (?, ?, ?, ?, ?)
            ''', ('BDG123', 'John Doe', 'officer@example.com', 'password123', 'Cyber Crime'))
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
        
    except Exception as e:
        logger.error(f"❌ Database init error: {e}")

init_db()

def generate_frames():
    global camera, scanning_active
    while True:
        try:
            with camera_lock:
                if scanning_active and camera and camera.isOpened():
                    success, frame = camera.read()
                    if success:
                        # Fix orientation
                        frame = cv2.flip(frame, 1)
                        
                        # Face recognition
                        matches = face_system.recognize_faces(frame)
                        
                        # Draw rectangles
                        for match in matches:
                            x, y, w, h = match['location']
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            label = f"{match['name']} {match['confidence']}%"
                            cv2.putText(frame, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        ret, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    else:
                        # Error frame
                        frame = np.zeros((480, 640, 3), np.uint8)
                        cv2.putText(frame, "Camera Error", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                        ret, buffer = cv2.imencode('.jpg', frame)
                        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                else:
                    # Waiting frame
                    frame = np.zeros((480, 640, 3), np.uint8)
                    cv2.putText(frame, "Start Scanning to Begin", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    ret, buffer = cv2.imencode('.jpg', frame)
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.03)
            
        except Exception as e:
            logger.error(f"Frame error: {e}")
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        conn = sqlite3.connect('sentinel.db')
        c = conn.cursor()
        c.execute("SELECT * FROM officers WHERE badge_id = ? AND password = ?", (data.get('badge_id'), data.get('password')))
        officer = c.fetchone()
        conn.close()
        
        if officer:
            session['officer_id'] = officer[0]
            session['officer_name'] = officer[2]
            return jsonify({'success': True})
        return jsonify({'success': False})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False})

@app.route('/dashboard')
def dashboard():
    if 'officer_id' not in session:
        return redirect('/')
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    global camera, scanning_active
    with camera_lock:
        scanning_active = False
        if camera:
            camera.release()
            camera = None
    session.clear()
    return redirect('/')

@app.route('/api/criminals', methods=['GET', 'POST'])
def manage_criminals():
    if 'officer_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        conn = sqlite3.connect('sentinel.db')
        c = conn.cursor()
        
        if request.method == 'GET':
            c.execute("SELECT * FROM criminals")
            criminals = c.fetchall()
            result = []
            for criminal in criminals:
                result.append({
                    'id': criminal[0],
                    'criminal_id': criminal[1],
                    'name': criminal[2],
                    'image_path': criminal[3],
                    'offenses': criminal[4],
                    'risk_level': criminal[5]
                })
            conn.close()
            return jsonify(result)
        
        elif request.method == 'POST':
            try:
                image_file = request.files['image']
                criminal_id = request.form['criminal_id']
                name = request.form['name']
                offenses = request.form['offenses']
                risk_level = request.form['risk_level']
                
                filename = f"{criminal_id}_{secure_filename(image_file.filename)}"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image_file.save(image_path)
                
                c.execute("INSERT INTO criminals (criminal_id, name, image_path, offenses, risk_level) VALUES (?, ?, ?, ?, ?)",
                         (criminal_id, name, image_path, offenses, risk_level))
                conn.commit()
                conn.close()
                
                if face_system.add_criminal_face(criminal_id, name, image_path):
                    return jsonify({'success': True, 'message': 'Criminal added successfully'})
                else:
                    return jsonify({'success': False, 'message': 'Face not detected'})
                    
            except Exception as e:
                conn.close()
                return jsonify({'success': False, 'message': str(e)})
                
    except Exception as e:
        logger.error(f"Criminals API error: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/stats')
def get_stats():
    """Return dummy stats - always works"""
    return jsonify({
        'criminal_count': 3,
        'matches_today': 1,
        'pending_verifications': 0,
        'system_accuracy': 85.0
    })

@app.route('/api/alerts')
def get_alerts():
    """Return empty alerts for now"""
    return jsonify([])

@app.route('/api/matches')
def get_matches():
    """Return empty matches for now"""
    return jsonify([])

def start_face_detection():
    global camera, scanning_active
    last_match_time = {}
    
    logger.info("🔍 Face detection started")
    
    while scanning_active:
        try:
            if not camera or not camera.isOpened():
                break
                
            success, frame = camera.read()
            if not success:
                time.sleep(0.5)
                continue
            
            # Fix orientation for detection too
            frame = cv2.flip(frame, 1)
            matches = face_system.recognize_faces(frame)
            current_time = time.time()
            
            for match in matches:
                criminal_id = match['criminal_id']
                
                #  only alert every 10 seconds per criminal
                if criminal_id in last_match_time and current_time - last_match_time[criminal_id] < 10:
                    continue
                
                last_match_time[criminal_id] = current_time
                
                # Send real-time alert via WebSocket
                socketio.emit('alert', {
                    'criminal_name': match['name'],
                    'confidence': match['confidence'],
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                })
                
                logger.info(f"📢 ALERT SENT: {match['name']} - {match['confidence']}%")
            
            time.sleep(1)  
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            time.sleep(1)
    
    logger.info("🛑 Face detection stopped")

@socketio.on('start_scan')
def handle_start_scan(data):
    global camera, scanning_active
    
    try:
        with camera_lock:
            if camera:
                camera.release()
            
            # Initialize camera
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                # Try different index
                camera = cv2.VideoCapture(1)
            
            if camera.isOpened():
                scanning_active = True
                emit('scan_started', {'message': 'Camera started successfully'})
                
                # Start detection thread
                thread = threading.Thread(target=start_face_detection)
                thread.daemon = True
                thread.start()
                
                logger.info("📹 Camera started")
            else:
                emit('scan_error', {'message': 'Cannot access camera'})
                
    except Exception as e:
        logger.error(f"Start scan error: {e}")
        emit('scan_error', {'message': str(e)})

@socketio.on('stop_scan')
def handle_stop_scan():
    global camera, scanning_active
    with camera_lock:
        scanning_active = False
        if camera:
            camera.release()
            camera = None
    emit('scan_stopped', {'message': 'Scanning stopped'})
    logger.info("📹 Camera stopped")

if __name__ == '__main__':
    logger.info("🚀 Starting SentinelSight...")
    logger.info("🔑 Login: BDG123 / password123")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)