"""
import socket
import struct
import face_recognition
import numpy as np
import threading
import cv2
import json
import ssl
import os

PORT = 9999
known_face_encodings = []
known_face_names = []

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

def load_face_database():
    global known_face_encodings, known_face_names
    
    # List of faces to load with their identifiers
    faces_to_load = [
        {"file": "obama.jpg", "name": "Barack Obama"},
        {"file": "shibravi.jpg", "name": "Shibravi Nagesh"},
        {"file": "shreeya.jpg", "name": "Shreeya Methuku"},
        {"file": "shreya.jpg", "name": "Shreya Patil"},
        {"file": "shambhavi.jpg", "name": "Shambhavi P M"}
        ]
    
    success_count = 0
    
    for face in faces_to_load:
        try:
            # Try multiple potential paths
            potential_paths = [
                face["file"],  # Try direct path first
                os.path.join(script_dir, face["file"]),  # Try script directory
                os.path.join(os.getcwd(), face["file"])  # Try current working directory
            ]
            
            # Also check if user provided a full path
            if os.path.isabs(face["file"]):
                potential_paths.insert(0, face["file"])
            
            loaded = False
            for path in potential_paths:
                if os.path.exists(path):
                    print(f"📷 Loading face from: {path}")
                    img = face_recognition.load_image_file(path)
                    encodings = face_recognition.face_encodings(img)
                    
                    if len(encodings) > 0:
                        encoding = encodings[0]
                        known_face_encodings.append(encoding)
                        known_face_names.append(face["name"])
                        success_count += 1
                        loaded = True
                        break
                    else:
                        print(f"⚠️ No faces found in {path}")
            
            if not loaded:
                print(f"❌ Could not load face from any path for {face['name']}")
                print(f"   Tried paths: {potential_paths}")
                
        except Exception as e:
            print(f"❌ Error loading {face['file']}: {e}")
    
    return success_count

def handle_client(conn, addr):
    print(f"📥 Connection from {addr}")
    data_buffer = b""
    while True:
        try:
            # Read frame size (4 bytes)
            while len(data_buffer) < 4:
                packet = conn.recv(4096)
                if not packet:
                    print("❌ Disconnected")
                    return
                data_buffer += packet
            
            # Extract frame size and remove from buffer
            frame_size = struct.unpack(">L", data_buffer[:4])[0]
            data_buffer = data_buffer[4:]
            
            # Read complete frame
            while len(data_buffer) < frame_size:
                data_buffer += conn.recv(4096)
            
            # Extract frame data and update buffer
            frame_data = data_buffer[:frame_size]
            data_buffer = data_buffer[frame_size:]
            
            # Decode frame
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("⚠️ Frame decoding failed, skipping frame.")
                continue
            
            # Process for facial recognition (scale down for performance)
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces and encode them
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            recognized_names = []
            access_granted = False
            
            # Skip recognition if no known faces are loaded
            if len(known_face_encodings) == 0:
                print("⚠️ No face database loaded, skipping recognition")
            else:
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            access_granted = True
                    
                    recognized_names.append(name)
            
            # Respond with authentication result
            response = {
                "faces_detected": len(face_locations),
                "recognized": recognized_names,
                "access_granted": access_granted
            }
            
            response_bytes = json.dumps(response).encode()
            size_bytes = struct.pack(">L", len(response_bytes))
            conn.sendall(size_bytes + response_bytes)
            
            print(f"✅ Faces Detected: {recognized_names}, Access: {'Granted' if access_granted else 'Denied'}")
            
        except Exception as e:
            print(f"💥 Error: {e}")
            break
    
    conn.close()

def main():
    try:
        print("🔍 Starting facial recognition server...")
        
        # Load face database
        success_count = load_face_database()
        if success_count > 0:
            print(f"✅ Loaded {success_count} faces into the database")
        else:
            print("⚠️ No faces loaded. The system will run but won't recognize anyone.")
            print("   Place face images in the same directory as this script or provide full paths.")
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', PORT))
        server_socket.listen(5)
        print(f"🚀 Server listening on port {PORT}")
        
        # Create SSL context for secure connections
        # Uncomment these lines after generating certificates
        # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        # wrapped_socket = context.wrap_socket(server_socket, server_side=True)
        
        while True:
            conn, addr = server_socket.accept()
            # For secure connection:
            # conn, addr = wrapped_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("🛑 Server shutting down...")
    except Exception as e:
        print(f"💥 Server error: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()

if __name__ == "__main__":
    main()
"""
import sys
# Add the models path to the system path
# Replace the path below with the 'Location' from 'pip show face-recognition-models'
sys.path.append(r" C:\Users\shree\AppData\Local\Programs\Python\Python313\Lib\site-packages") 
import socket
import struct
import face_recognition
import numpy as np
import threading
import cv2
import json
import ssl
import os
import pickle
import time

PORT = 9999
DATABASE_FILE = "face_database.pkl"

def load_face_database():
    """Load the face database from file"""
    if os.path.exists(DATABASE_FILE):
        try:
            with open(DATABASE_FILE, "rb") as f:
                database = pickle.load(f)
                print(f"✅ Loaded face database with {len(database['names'])} faces")
                return database["encodings"], database["names"]
        except Exception as e:
            print(f"❌ Error loading face database: {e}")
    
    # If file doesn't exist or there's an error, check for image files
    print("⚠️ Database file not found, trying to load from image files...")
    return load_from_image_files()

def load_from_image_files():
    """Legacy method to load faces from individual image files"""
    known_face_encodings = []
    known_face_names = []
    
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of faces to load with their identifiers
    faces_to_load = [
        {"file": "obama.jpg", "name": "Barack Obama"},
        {"file": "shibravi.jpg", "name": "Shibravi Nagesh"}
    ]
    
    success_count = 0
    
    for face in faces_to_load:
        try:
            # Try multiple potential paths
            potential_paths = [
                face["file"],  # Try direct path first
                os.path.join(script_dir, face["file"]),  # Try script directory
                os.path.join(os.getcwd(), face["file"])  # Try current working directory
            ]
            
            # Also check if user provided a full path
            if os.path.isabs(face["file"]):
                potential_paths.insert(0, face["file"])
            
            loaded = False
            for path in potential_paths:
                if os.path.exists(path):
                    print(f"📷 Loading face from: {path}")
                    img = face_recognition.load_image_file(path)
                    encodings = face_recognition.face_encodings(img)
                    
                    if len(encodings) > 0:
                        encoding = encodings[0]
                        known_face_encodings.append(encoding)
                        known_face_names.append(face["name"])
                        success_count += 1
                        loaded = True
                        break
                    else:
                        print(f"⚠️ No faces found in {path}")
            
            if not loaded:
                print(f"❌ Could not load face from any path for {face['name']}")
                
        except Exception as e:
            print(f"❌ Error loading {face['file']}: {e}")
    
    print(f"✅ Loaded {success_count} faces from image files")
    return known_face_encodings, known_face_names

def handle_client(conn, addr, known_face_encodings, known_face_names):
    print(f"📥 Connection from {addr}")
    data_buffer = b""
    while True:
        try:
            # Read frame size (4 bytes)
            while len(data_buffer) < 4:
                packet = conn.recv(4096)
                if not packet:
                    print("❌ Disconnected")
                    return
                data_buffer += packet
            
            # Extract frame size and remove from buffer
            frame_size = struct.unpack(">L", data_buffer[:4])[0]
            data_buffer = data_buffer[4:]
            
            # Read complete frame
            while len(data_buffer) < frame_size:
                data_buffer += conn.recv(4096)
            
            # Extract frame data and update buffer
            frame_data = data_buffer[:frame_size]
            data_buffer = data_buffer[frame_size:]
            
            # Decode frame
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                print("⚠️ Frame decoding failed, skipping frame.")
                continue
            
            # Process for facial recognition (scale down for performance)
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find faces and encode them
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            recognized_names = []
            access_granted = False
            # Convert face locations to the original frame size for better visualization
            scaled_face_locations = []
            
            # Skip recognition if no known faces are loaded
            if len(known_face_encodings) == 0:
                print("⚠️ No face database loaded, skipping recognition")
                for (top, right, bottom, left) in face_locations:
                    # Scale back to original frame size
                    scaled_face_locations.append({
                        "top": top * 4,
                        "right": right * 4,
                        "bottom": bottom * 4,
                        "left": left * 4
                    })
            else:
                for i, face_encoding in enumerate(face_encodings):
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]
                            access_granted = True
                    
                    recognized_names.append(name)
                    
                    # Scale back to original frame size
                    top, right, bottom, left = face_locations[i]
                    scaled_face_locations.append({
                        "top": top * 4,
                        "right": right * 4,
                        "bottom": bottom * 4,
                        "left": left * 4
                    })
            
            # Log access attempts
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            if access_granted:
                # Log successful access
                with open("access_log.txt", "a") as log_file:
                    recognized_names_str = ", ".join(recognized_names) or "Unknown"
                    log_file.write(f"{timestamp}: Access GRANTED for {recognized_names_str} from {addr}\n")
                
                # Here you would trigger your access control system
                # For example, send a signal to unlock a door
                # unlock_door()  # You would implement this function
            else:
                # Log failed access attempt
                with open("access_log.txt", "a") as log_file:
                    log_file.write(f"{timestamp}: Access DENIED for unknown person from {addr}\n")
            
            # Respond with authentication result
            response = {
                "faces_detected": len(face_locations),
                "recognized": recognized_names,
                "access_granted": access_granted,
                "timestamp": timestamp,
                "face_locations": scaled_face_locations  # Send face locations for client-side visualization
            }
            
            response_bytes = json.dumps(response).encode()
            size_bytes = struct.pack(">L", len(response_bytes))
            conn.sendall(size_bytes + response_bytes)
            
            print(f"✅ Faces Detected: {recognized_names}, Access: {'Granted' if access_granted else 'Denied'}")
            
        except Exception as e:
            print(f"💥 Error: {e}")
            break
    
    conn.close()

def main():
    try:
        print("🔍 Starting facial recognition security system...")
        
        # Load face database
        known_face_encodings, known_face_names = load_face_database()
        
        if len(known_face_encodings) > 0:
            print(f"✅ Loaded {len(known_face_encodings)} faces into the database")
        else:
            print("⚠️ No faces loaded. The system will run but won't recognize anyone.")
            print("   Run the database management tool to add faces.")
        
        # Create server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('', PORT))
        server_socket.listen(5)
        print(f"🚀 Server listening on port {PORT}")
        
        # Create SSL context for secure connections
        # Uncomment these lines after generating certificates
        # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # context.load_cert_chain(certfile="server.crt", keyfile="server.key")
        # wrapped_socket = context.wrap_socket(server_socket, server_side=True)
        
        while True:
            conn, addr = server_socket.accept()
            # For secure connection:
            # conn, addr = wrapped_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr, known_face_encodings, known_face_names))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("🛑 Server shutting down...")
    except Exception as e:
        print(f"💥 Server error: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()

if __name__ == "__main__":
    main()