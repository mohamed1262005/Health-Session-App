import sys
import cv2
import time
import threading
import numpy as np
import mediapipe as mp
import platform

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox, QSpinBox
)
from PyQt5.QtGui import QImage, QPixmap, QFont

# ------------------------------ Mediapipe Setup ------------------------------
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

def play_alert_sound():
    try:
        if platform.system() == "Windows":
            import winsound
            winsound.Beep(1000, 500)
        else:
            print("\a")
    except:
        pass

def get_available_cameras():
    available_cameras = []
    for i in range(3):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if platform.system()=="Windows" else cv2.CAP_ANY)
        if cap.isOpened():
            available_cameras.append(f"Camera {i}")
            cap.release()
    if not available_cameras:
        available_cameras.append("Camera 0")
    return available_cameras

# ========================================= MAIN APP =========================================
class PostureApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Posture Monitor - AI Edition (by Mohamed)")
        self.setGeometry(200, 100, 1000, 850)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; }
            QPushButton { padding: 10px; font-size: 14px; font-weight: bold; border-radius: 8px; color: white; }
            QComboBox, QSpinBox { padding: 8px; font-size: 14px; border-radius: 8px; background-color: #313244; color: white; border: 1px solid #45475a; }
            QLabel { font-weight: bold; }
        """)

        # ---------------- UI ----------------
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(960, 540)
        self.camera_label.setStyleSheet("background-color: #000; border: 2px solid #45475a; border-radius: 10px;")
        
        self.status_label = QLabel("Status: Waiting...")
        self.status_label.setFont(QFont("Arial", 18))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #89b4fa; padding: 5px;")

        # Metrics
        metrics_layout = QHBoxLayout()
        self.neck_label = QLabel("Neck Angle: -")
        self.torso_label = QLabel("Torso Angle: -")
        self.side_label = QLabel("Side: -")
        self.timer_label = QLabel("Work Timer: 00:00 | Breaks: 0")

        for lbl in [self.neck_label, self.torso_label, self.side_label, self.timer_label]:
            lbl.setFont(QFont("Arial", 12))
            lbl.setStyleSheet("background-color: #313244; padding: 8px; border-radius: 5px;")
            metrics_layout.addWidget(lbl)

        # --- Controls Area ---
        controls_layout = QHBoxLayout()

        # Camera Selector
        self.camera_selector = QComboBox()
        self.camera_selector.addItems(get_available_cameras())
        self.camera_selector.setFixedWidth(150)

        # Work Time
        self.work_time_input = QSpinBox()
        self.work_time_input.setRange(1, 120)
        self.work_time_input.setValue(25)
        self.work_time_input.setSuffix(" min")

        # Break Time
        self.break_time_input = QSpinBox()
        self.break_time_input.setRange(1, 60)
        self.break_time_input.setValue(5)
        self.break_time_input.setSuffix(" min")

        # Alert Time
        self.alert_time_input = QSpinBox()
        self.alert_time_input.setRange(1, 60)
        self.alert_time_input.setValue(5)
        self.alert_time_input.setSuffix(" sec")

        # Buttons
        self.start_btn = QPushButton("Start Camera")
        self.start_btn.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e;")
        self.start_btn.clicked.connect(self.start_camera)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        self.stop_btn.clicked.connect(self.stop_camera)

        self.report_btn = QPushButton("Show Report")
        self.report_btn.setStyleSheet("background-color: #89b4fa; color: #1e1e2e;")
        self.report_btn.clicked.connect(self.show_report)

        # Break Button
        self.break_btn = QPushButton("Take Break")
        self.break_btn.setStyleSheet("background-color: #fab387; color: #1e1e2e;")
        self.break_btn.clicked.connect(self.take_break)

        # Add to layout
        controls_layout.addWidget(QLabel("Camera:"))
        controls_layout.addWidget(self.camera_selector)
        controls_layout.addWidget(QLabel("Work Time:"))
        controls_layout.addWidget(self.work_time_input)
        controls_layout.addWidget(QLabel("Break Time:"))
        controls_layout.addWidget(self.break_time_input)
        controls_layout.addWidget(QLabel("Alert Time:"))
        controls_layout.addWidget(self.alert_time_input)
        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.break_btn)
        controls_layout.addWidget(self.report_btn)

        # Main Layout
        layout = QVBoxLayout()
        layout.addWidget(self.camera_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.status_label)
        layout.addLayout(metrics_layout)
        layout.addLayout(controls_layout)
        self.setLayout(layout)

        # ---------------- Logic ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.cap = None
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.bad_posture_start = None

        self.work_duration = 25*60
        self.break_duration = 5*60
        self.work_remaining = self.work_duration
        self.break_remaining = self.break_duration
        self.in_break = False
        self.break_taken_count = 0

        self.ALERT_THRESHOLD = 5

        self.history_data = []
        self.last_record_time = time.time()

        self.break_timer = QTimer()
        self.break_timer.timeout.connect(self._tick)

    # ---------------- Camera ----------------
    def start_camera(self):
        if self.cap: return

        cam_text = self.camera_selector.currentText()
        cam_index = int(cam_text.split(" ")[1])
        self.cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW if platform.system()=="Windows" else cv2.CAP_ANY)
        
        if not self.cap.isOpened():
            self.status_label.setText("Error: Cannot open selected camera")
            return
        
        # قراءة إعدادات المستخدم
        self.work_duration = self.work_time_input.value() * 60
        self.break_duration = self.break_time_input.value() * 60
        self.work_remaining = self.work_duration
        self.break_remaining = self.break_duration
        self.ALERT_THRESHOLD = self.alert_time_input.value()

        self.status_label.setText("Status: Camera Active")
        self.timer.start(30)
        self.break_timer.start(1000)

    def stop_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.timer.stop()
        self.break_timer.stop()
        self.camera_label.clear()
        self.status_label.setText("Status: Stopped")
        self.neck_label.setText("Neck Angle: -")
        self.torso_label.setText("Torso Angle: -")
        self.timer_label.setText("Work Timer: 00:00 | Breaks: 0")

    # ---------------- Manual Break ----------------
    def take_break(self):
        self.break_taken_count += 1
        threading.Thread(target=play_alert_sound, daemon=True).start()
        QMessageBox.information(self, "Break Taken", f"تم أخذ بريك يدوي ✅\nعدد الاسترحات: {self.break_taken_count}")
        self.update_timer_label()

    # ---------------- Break Timer ----------------
    def _tick(self):
        if self.in_break:
            self.break_remaining -= 1
            if self.break_remaining <= 0:
                self.in_break = False
                self.work_remaining = self.work_duration
                self.break_remaining = self.break_duration
                self.break_taken_count += 1
                threading.Thread(target=play_alert_sound, daemon=True).start()
                QMessageBox.information(self, "Break Over", f"Break finished! العودة للعمل\nعدد البريكات: {self.break_taken_count}")
        else:
            self.work_remaining -= 1
            if self.work_remaining <= 0:
                self.in_break = True
                self.break_remaining = self.break_duration
                threading.Thread(target=play_alert_sound, daemon=True).start()
                QMessageBox.information(self, "Time for Break", f"حان وقت الاستراحة!\nعدد البريكات: {self.break_taken_count}")
        self.update_timer_label()

    def update_timer_label(self):
        if self.in_break:
            mins = self.break_remaining // 60
            secs = self.break_remaining % 60
            self.timer_label.setText(f"Break: {mins:02d}:{secs:02d} | Breaks: {self.break_taken_count}")
            self.timer_label.setStyleSheet("background-color: #a6e3a1; color: #1e1e2e; padding: 8px; border-radius: 5px;")
        else:
            mins = self.work_remaining // 60
            secs = self.work_remaining % 60
            self.timer_label.setText(f"Work: {mins:02d}:{secs:02d} | Breaks: {self.break_taken_count}")
            self.timer_label.setStyleSheet("background-color: #313244; color: #cdd6f4; padding: 8px; border-radius: 5px;")

    # ---------------- Frame Update ----------------
    def update_frame(self):
        if not self.cap: return
        ret, frame = self.cap.read()
        if not ret: return

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose.process(rgb)
        rgb.flags.writeable = True

        h, w, _ = frame.shape
        current_status_good = False

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            l_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            r_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            is_left_side = l_shoulder.visibility > r_shoulder.visibility

            if is_left_side:
                self.side_label.setText("Side: LEFT")
                ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
                shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
            else:
                self.side_label.setText("Side: RIGHT")
                ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value]
                shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

            neck_angle = calculate_angle(ear, shoulder, hip)
            vertical_point = Point(hip.x, hip.y - 0.5)
            torso_angle = calculate_angle(vertical_point, hip, shoulder)

            self.neck_label.setText(f"Neck: {int(neck_angle)}°")
            self.torso_label.setText(f"Torso: {int(torso_angle)}°")

            is_neck_good = neck_angle > 145
            is_torso_good = torso_angle < 20

            if is_neck_good and is_torso_good:
                current_status_good = True
                self.status_label.setText("Status: Good Posture ✅")
                self.status_label.setStyleSheet("color: #a6e3a1; padding:5px;")
                self.bad_posture_start = None
                color = (0, 255, 0)
            else:
                current_status_good = False
                msg = "Fix: "
                if not is_neck_good: msg += "Head! "
                if not is_torso_good: msg += "Back! "
                self.status_label.setText(msg)
                self.status_label.setStyleSheet("color: #f38ba8; padding:5px;")

                if self.bad_posture_start is None:
                    self.bad_posture_start = time.time()
                elif time.time() - self.bad_posture_start > self.ALERT_THRESHOLD:
                    threading.Thread(target=play_alert_sound, daemon=True).start()
                    self.bad_posture_start = time.time()
                color = (0, 0, 255)

            # mp_drawing.draw_landmarks(
            #     frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            #     mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2),
            #     mp_drawing.DrawingSpec(color=color, thickness=2, circle_radius=2)
            # )
        else:
            self.status_label.setText("Waiting for person...")

        current_time = time.time()
        if current_time - self.last_record_time >= 1.0:
            self.history_data.append({'time': current_time, 'is_good': current_status_good})
            self.last_record_time = current_time

        frame_rgb_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        qt_image = QImage(frame_rgb_display.data, w, h, frame_rgb_display.strides[0], QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(qt_image).scaled(self.camera_label.width(), self.camera_label.height(), Qt.KeepAspectRatio)
        self.camera_label.setPixmap(pix)

    # ---------------- History Report ----------------
    def show_report(self):
        if not self.history_data:
            QMessageBox.information(self, "Report", "No data collected yet.\nابدأ الكاميرا أولاً")
            return

        now = time.time()
        last_30_min_data = [d for d in self.history_data if now - d['time'] <= 1800]

        if not last_30_min_data:
            QMessageBox.information(self, "Report", "No recent data.")
            return

        total_seconds = len(last_30_min_data)
        good_seconds = sum(1 for d in last_30_min_data if d['is_good'])
        bad_seconds = total_seconds - good_seconds
        good_percentage = (good_seconds / total_seconds) * 100 if total_seconds > 0 else 0

        total_mins = total_seconds / 60
        good_mins = good_seconds / 60

        report_text = (
            f"--- Posture Report (Last {int(total_mins)} mins) ---\n\n"
            f"✅ Good Time: {good_mins:.1f} min\n"
            f"⚠️ Bad Time: {(bad_seconds/60):.1f} min\n"
            f"📊 Score: {good_percentage:.1f}%\n"
            f"🕒 Breaks Taken: {self.break_taken_count}\n"
        )
        
        QMessageBox.information(self, "Performance Summary", report_text)


# ========================================= RUN APP =========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PostureApp()
    window.show()
    sys.exit(app.exec_())
