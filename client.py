"""
import socket
import cv2
import struct
import time
import threading

SERVER_IP = '127.0.0.1'  # Change to server IP if remote
PORT = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))
print("✅ Connected to server")

def send_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access webcam")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Resize & compress frame
        small_frame = cv2.resize(frame, (0, 0), fx=0.3, fy=0.3)
        _, buffer = cv2.imencode('.jpg', small_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        data = buffer.tobytes()

        # Send with length prefix
        client_socket.sendall(struct.pack('>L', len(data)) + data)

        # Display local camera view
        cv2.imshow('Client View', small_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(0.1)  # 10 FPS max

    cap.release()
    client_socket.close()
    cv2.destroyAllWindows()

send_frames()
"""


import socket
import struct
import face_recognition 
import socket
import cv2
import struct
import time
import threading
import json
import ssl
import numpy as np
import os

SERVER_IP = '127.0.0.1'  # Change to server IP if remote
PORT = 9999
RECONNECT_DELAY = 5  # Seconds to wait before reconnecting

# Get user's home directory
HOME_DIR = os.path.expanduser('~')
# Define cascade file path in the user's home directory
CASCADE_PATH = os.path.join(HOME_DIR, 'haarcascade_frontalface_default.xml')

class FaceRecognitionClient:
    def __init__(self, server_ip, port, cascade_path=CASCADE_PATH):
        self.server_ip = server_ip
        self.port = port
        self.connected = False
        self.client_socket = None
        self.access_status = "Not connected"
        self.recognized_names = []
        self.running = True
        self.face_locations = []
        self.last_response_time = time.time()
        self.cascade_path = cascade_path

    def connect_to_server(self):
        while self.running:
            try:
                # Create new socket
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # For secure connection:
                # context = ssl.create_default_context()
                # context.check_hostname = False
                # context.verify_mode = ssl.CERT_NONE
                # self.client_socket = context.wrap_socket(self.client_socket, server_hostname=self.server_ip)
                
                self.client_socket.connect((self.server_ip, self.port))
                print("✅ Connected to server")
                self.connected = True
                
                # Start response receiver thread
                response_thread = threading.Thread(target=self.receive_responses)
                response_thread.daemon = True
                response_thread.start()
                
                # Start sending frames
                self.send_frames()
            except ConnectionRefusedError:
                print(f"❌ Connection refused. Retrying in {RECONNECT_DELAY} seconds...")
                time.sleep(RECONNECT_DELAY)
            except Exception as e:
                print(f"❌ Connection error: {e}")
                time.sleep(RECONNECT_DELAY)
            finally:
                self.connected = False
                if self.client_socket:
                    self.client_socket.close()
                    self.client_socket = None
                if self.running:
                    print(f"♻️ Reconnecting in {RECONNECT_DELAY} seconds...")
                    time.sleep(RECONNECT_DELAY)

    def receive_responses(self):
        data_buffer = b""
        while self.connected:
            try:
                # Read response size (4 bytes)
                while len(data_buffer) < 4:
                    packet = self.client_socket.recv(4096)
                    if not packet:
                        print("❌ Server disconnected")
                        self.connected = False
                        return
                    data_buffer += packet
                
                # Extract response size and remove from buffer
                response_size = struct.unpack(">L", data_buffer[:4])[0]
                data_buffer = data_buffer[4:]
                
                # Read complete response
                while len(data_buffer) < response_size:
                    data_buffer += self.client_socket.recv(4096)
                
                # Extract response data and update buffer
                response_data = data_buffer[:response_size]
                data_buffer = data_buffer[response_size:]
                
                # Parse response
                response = json.loads(response_data.decode())
                self.recognized_names = response.get("recognized", [])
                self.access_status = "Access Granted" if response.get("access_granted", False) else "Access Denied"
                self.face_locations = response.get("face_locations", [])
                self.last_response_time = time.time()
                print(f"👤 Recognized: {self.recognized_names} - {self.access_status}")
            except Exception as e:
                print(f"💥 Error receiving response: {e}")
                self.connected = False
                break

    def detect_faces_locally(self, frame):
        """Detect faces locally as a fallback if server doesn't provide locations"""
        try:
            # Check if cascade file exists
            if not os.path.isfile(self.cascade_path):
                print(f"❌ Error: Haar cascade file not found at {self.cascade_path}")
                return []
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Use the specific path to the Haar cascade file
            face_cascade = cv2.CascadeClassifier(self.cascade_path)
            
            # Check if classifier loaded successfully
            if face_cascade.empty():
                print("❌ Error: Haar cascade file could not be loaded. Check the file path.")
                return []
                
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            # Convert to the same format as server face locations
            face_locations = []
            for (x, y, w, h) in faces:
                face_locations.append({
                    "top": y,
                    "right": x + w,
                    "bottom": y + h,
                    "left": x
                })
            return face_locations
        except Exception as e:
            print(f"❌ Error detecting faces locally: {e}")
            return []

    def send_frames(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot access webcam")
            return
        
        try:
            while self.connected and self.running:
                ret, frame = cap.read()
                if not ret:
                    continue
                
                # Create a copy for display
                display_frame = frame.copy()
                
                # Use server face locations or detect locally as fallback
                face_locations = self.face_locations
                if not face_locations and time.time() - self.last_response_time > 1.0:
                    face_locations = self.detect_faces_locally(frame)
                
                # Draw face boxes and names
                for i, face_loc in enumerate(face_locations):
                    # Extract coordinates
                    top = face_loc["top"]
                    right = face_loc["right"]
                    bottom = face_loc["bottom"]
                    left = face_loc["left"]
                    
                    # Determine the name and access status
                    name = "Unknown"
                    if i < len(self.recognized_names):
                        name = self.recognized_names[i]
                    
                    # Set colors based on recognition
                    if name != "Unknown" and self.access_status == "Access Granted":
                        color = (0, 255, 0)  # Green for recognized & granted
                    else:
                        color = (0, 0, 255)  # Red for unrecognized or denied
                    
                    # Draw rectangle around the face
                    cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                    
                    # Draw filled rectangle for text background
                    cv2.rectangle(display_frame, (left, bottom), (right, bottom+30), color, cv2.FILLED)
                    
                    # Put name text
                    cv2.putText(display_frame, name, (left+5, bottom+25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Display access status
                status_color = (0, 255, 0) if self.access_status == "Access Granted" else (0, 0, 255)
                
                # Draw status bar at the top
                cv2.rectangle(display_frame, (0, 0), (frame.shape[1], 40), (0, 0, 0), cv2.FILLED)
                cv2.putText(display_frame, self.access_status, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
                
                # Resize & compress frame for sending
                small_frame = cv2.resize(frame, (0, 0), fx=0.3, fy=0.3)
                _, buffer = cv2.imencode('.jpg', small_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                data = buffer.tobytes()
                
                # Send with length prefix
                try:
                    self.client_socket.sendall(struct.pack('>L', len(data)) + data)
                except Exception as e:
                    print(f"💥 Error sending frame: {e}")
                    break
                
                # Display the frame with overlays
                cv2.imshow('Face Recognition System', display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(0.1)  # 10 FPS max
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.running = False

    def stop(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()

if __name__ == "__main__":
    # Check if cascade file exists, if not, download it
    if not os.path.isfile(CASCADE_PATH):
        print(f"Haar cascade file not found. Downloading to {CASCADE_PATH}...")
        import urllib.request
        url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        try:
            urllib.request.urlretrieve(url, CASCADE_PATH)
            print("✅ Downloaded successfully!")
        except Exception as e:
            print(f"❌ Failed to download: {e}")
            exit(1)
    
    client = FaceRecognitionClient(SERVER_IP, PORT)
    try:
        client.connect_to_server()
    except KeyboardInterrupt:
        print("🛑 Client shutting down...")
    finally:
        client.stop()