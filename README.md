Smart Posture Monitor - AI Edition 🧘‍♂️💻
Smart Posture Monitor is an advanced AI-powered desktop application designed to monitor your sitting posture in real-time. Built with Python, OpenCV, and MediaPipe, it helps prevent back and neck pain by alerting you when you slouch and encouraging healthy sitting habits through a built-in Pomodoro-style timer.

✨ Features
AI Pose Estimation: High-precision tracking of neck and torso angles using the MediaPipe pose model.

Real-time Posture Correction: Instant visual and audio alerts when bad posture is detected for more than a few seconds.

Integrated Work/Break Timer: Customizable Pomodoro timer (Work/Break cycles) to ensure you take regular rests.

Performance Reports: Detailed session summary showing the percentage of "Good Posture" time and total breaks taken.

Multi-Camera Support: Easily switch between integrated and external cameras.

Cross-Platform: Styled with a modern "Catppuccin" dark theme for a sleek look on Windows, Linux, and macOS.

⚠️ Recommended Setup
[!IMPORTANT] External Camera Highly Recommended: For the best accuracy in angle calculation, it is highly recommended to use an External Webcam placed at a side view (90-degree profile). This allows the AI to accurately measure the alignment of your ear, shoulder, and hip.

🛠 Tech Stack
Language: Python 3.x

GUI Framework: PyQt5

Computer Vision: OpenCV

AI Engine: MediaPipe (Pose Landmark Detection)

Mathematics: NumPy (Trigonometric angle calculations)

🚀 Getting Started
1. Prerequisites
Ensure you have Python installed, then install the required dependencies:

Bash

pip install opencv-python mediapipe PyQt5 numpy
2. Installation & Run
Clone the repository:

Bash

git clone https://github.com/YourUsername/Smart-Posture-Monitor.git
Navigate to the folder:

Bash

cd Smart-Posture-Monitor
Launch the application:

Bash

python main.py
📈 How It Works
The application calculates two primary angles to determine posture quality:

Neck Angle: Measured between the Ear, Shoulder, and Hip. (Threshold: > 145°)

Torso Angle: Measured between the Shoulder, Hip, and a vertical reference line. (Threshold: < 20°)

🤝 Contribution
Contributions, issues, and feature requests are welcome! Feel free to check the issues page if you want to contribute.

📝 License
This project is licensed under the MIT License.
Download & Run (No Coding Required)
If you just want to use the application without dealing with the source code, follow these steps:

Go to the Releases page on the right side of this repository.

Download the latest version of SmartPostureMonitor.zip or .exe.

Extract the folder (if zipped) and double-click SmartPostureMonitor.exe.

Note: Your Windows Defender might show a "Windows protected your PC" message because the app is not digitally signed. Click "More info" and then "Run anyway".

Developed with ❤️ by Mohamed
