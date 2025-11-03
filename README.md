Real-Time Facial Recognition Security System
This project is a client-server application that provides real-time facial recognition for security and access control. The client captures video from a webcam, streams it to a server, and the server processes the feed to identify individuals against a database of known faces, granting or denying access accordingly.

How It Works
The system operates on a client-server model:

Server (server.py): This script is the core of the system. It listens for incoming client connections, receives video frames, and performs facial recognition. When a face is detected, it is compared against a pre-loaded database of known individuals. The server then sends a response back to the client indicating whether access is granted or denied, along with the names of recognized people.​

Client (client.py): This script connects to the server, captures video from a webcam, and sends the frames for processing. It then receives the server's analysis and overlays the information onto the live video feed. This includes drawing bounding boxes around faces, displaying the recognized name, and showing the current access status ("Access Granted" or "Access Denied").​

Key Features
Real-Time Recognition: Performs facial recognition on a live video stream.

Client-Server Architecture: Offloads heavy processing to the server, allowing the client to be lightweight.

Dynamic Face Database: The server loads known faces from image files at startup.​

Access Logging: The server maintains a text file (access_log.txt) to log all granted and denied access attempts with timestamps.​

Visual Feedback: The client provides immediate visual feedback, including bounding boxes and status messages.​

Robust Connectivity: The client will automatically attempt to reconnect to the server if the connection is lost.​

Local Fallback: If the server response is delayed, the client can perform local face detection using a Haar cascade to keep the display responsive.​

Getting Started
Follow these instructions to set up and run the facial recognition system.

Requirements
You will need Python 3 and the following libraries installed:

opencv-python

face-recognition

numpy

Installation
Clone or Download: Place server.py and client.py in the same directory.

Install Dependencies: Open your terminal or command prompt and install the required packages using pip:

bash
pip install opencv-python face-recognition numpy
Configuration
Populate the Face Database (Server)

To add authorized individuals, create image files (e.g., barack_obama.jpg, shreya_patil.jpg) for each person.

Place these image files in the same directory as the server.py script. The server will automatically detect and load these images on startup to build its database of known faces.​

Set the Server IP Address (Client)

If you are running the client and server on different computers, open client.py in a text editor.

Locate the line SERVER_IP = '127.0.0.1' and change the IP address to the network IP of the computer running server.py.​

Usage
Start the Server

Open a terminal, navigate to the project directory, and run the server script:

bash
python server.py
The server will load the face database and wait for a client to connect.​

Run the Client

Open a second terminal, navigate to the same directory, and run the client script:

bash
python client.py
A window will appear showing your webcam feed. When a face is detected, the system will display a bounding box and an access status message.

To stop the client, press the 'q' key while the video window is active
