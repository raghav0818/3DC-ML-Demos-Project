import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from dataclasses import dataclass
from collections import deque

@dataclass
class BiometricMetrics:
    ear: float
    lip_distance: float
    pitch: float
    yaw: float
    iris_velocity: float
    mouth_corner_dist: float # For smile

class BioStressDetector:
    def __init__(self):
        # MediaPipe Setup
        base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1)
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        
        # --- INDICES ---
        self.LEFT_EYE = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE = [362, 385, 387, 263, 373, 380]
        # Inner lips (Vertical) - 13, 14
        self.LIPS_VERTICAL = [13, 14]
        # Mouth Corners (Smile) - 61 (Left), 291 (Right)
        self.MOUTH_CORNERS = [61, 291]
        self.UPPER_LIP_CENTER = 0 # Tip of nose/lip junction for smile Ref
        # Iris - 468-472 (Left), 473-477 (Right)
        # Center of iris is usually inferred, but MP FaceMesh now has specific iris landmarks
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]

        # --- CALIBRATION ---
        self.is_calibrated = False
        self.calib_buffer = []
        
        # Stats (Mean + StdDev for Z-Score)
        self.stats = {
            "ear": {"mean": 0.0, "std": 0.0},
            "lip": {"mean": 0.0, "std": 0.0},
            "pitch": {"mean": 0.0, "std": 0.0},
            "yaw": {"mean": 0.0, "std": 0.0}
        }
        
        # --- RUNTIME STATE ---
        self.sensitivity = 1.0
        self.history = deque(maxlen=5) # Smoothing window
        self.prev_iris_pos = None # For velocity calc

    # --- GEOMETRY UTILS ---
    def _dist(self, p1, p2): # Euclidian normalized
        return np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p2.x, p2.y]))

    def _calculate_ear(self, landmarks, indices):
        # Vertical 1, Vertical 2, Horizontal
        v1 = self._dist(landmarks[indices[1]], landmarks[indices[5]])
        v2 = self._dist(landmarks[indices[2]], landmarks[indices[4]])
        hor = self._dist(landmarks[indices[0]], landmarks[indices[3]])
        return (v1 + v2) / (2.0 * hor) if hor > 0 else 0.0

    def _get_iris_center(self, landmarks, indices):
        # Average of iris points
        xs = [landmarks[i].x for i in indices]
        ys = [landmarks[i].y for i in indices]
        return (np.mean(xs), np.mean(ys))

    # --- CALIBRATION LOGIC ---
    def calibrate_frame(self, frame):
        metrics, _ = self.process_frame(frame)
        if metrics:
            self.calib_buffer.append(metrics)

    def finalize_calibration(self):
        if len(self.calib_buffer) < 10: return False
        
        # Calculate Mean & StdDev for Z-Score
        def calc_stat(key, func):
            data = [func(m) for m in self.calib_buffer]
            self.stats[key]["mean"] = np.mean(data)
            self.stats[key]["std"] = np.std(data)
            # Prevent divide by zero if user was perfectly still (0 std)
            if self.stats[key]["std"] < 0.001: self.stats[key]["std"] = 0.001
            
        calc_stat("ear", lambda m: m.ear)
        calc_stat("lip", lambda m: m.lip_distance)
        calc_stat("pitch", lambda m: m.pitch)
        calc_stat("yaw", lambda m: m.yaw)
        
        self.is_calibrated = True
        self.calib_buffer.clear()
        return True

    # --- PROCESSING ---
    def process_frame(self, frame):
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000)
        
        result = self.landmarker.detect_for_video(mp_img, ts)
        
        if not result.face_landmarks:
            return None, None
            
        params = result.face_landmarks[0]
        matrix = result.facial_transformation_matrixes
        
        # 1. EAR
        ear = (self._calculate_ear(params, self.LEFT_EYE) + 
               self._calculate_ear(params, self.RIGHT_EYE)) / 2.0
               
        # 2. Lip Distance (Normalized Y)
        lip_d = abs(params[13].y - params[14].y)
        
        # 3. Head Pose (Nose Tip Position as proxy if Matrix complex)
        # Using Nose Tip (1)
        pitch = params[1].y
        yaw = params[1].x
        
        # 4. Iris Velocity (Saccades)
        l_iris = self._get_iris_center(params, self.LEFT_IRIS)
        r_iris = self._get_iris_center(params, self.RIGHT_IRIS)
        avg_iris = ((l_iris[0] + r_iris[0])/2, (l_iris[1] + r_iris[1])/2)
        
        iris_vel = 0.0
        if self.prev_iris_pos:
            # Distance moved since last frame
            dist = np.linalg.norm(np.array(avg_iris) - np.array(self.prev_iris_pos))
            iris_vel = dist * 100 # Scale up for readability
        self.prev_iris_pos = avg_iris
        
        # 5. Smile (Mouth Corners Y vs Upper Lip Y)
        # If corners are significantly higher (smaller Y) than lip center
        lip_center_y = params[0].y # Upper lip
        corner_avg_y = (params[61].y + params[291].y) / 2.0
        # Positive if corners are ABOVE center (Smiling)
        smile_metric = lip_center_y - corner_avg_y 
        
        metrics = BiometricMetrics(ear, lip_d, pitch, yaw, iris_vel, smile_metric)
        return metrics, params

    # --- DETECTION LOGIC (Z-SCORE) ---
    def get_stress_score(self, frame):
        metrics, lms = self.process_frame(frame)
        if not metrics or not self.is_calibrated:
            return 0.0, frame, []
            
        reasons = []
        score = 0.0
        
        # Z-Score Helper
        def get_z(val, key):
            return abs(val - self.stats[key]["mean"]) / self.stats[key]["std"]
            
        # 1. SACCADES (Shifty Eyes) - High confidence
        # Velocity > 1.5 (Rapid movement) while Head Z-Score < 2 (Head still)
        # We don't want to trigger if whole head is moving
        head_motion = get_z(metrics.yaw, "yaw")
        if metrics.iris_velocity > 1.5 and head_motion < 2.0:
            score += 0.4
            reasons.append("SACCADIC MASKING")
            
        # 2. LAUGHTER FILTER
        # If smile metric > 0.02, user is likely smiling/laughing
        is_smiling = metrics.mouth_corner_dist > 0.02
        
        if not is_smiling:
            # 3. LIP COMPRESSION (Only if not smiling)
            # Z-Score > 2.5 (Significant deviation)
            z_lip = (self.stats["lip"]["mean"] - metrics.lip_distance) / self.stats["lip"]["std"]
            # Note: We care if distance is SMALLER (compression), so (Mean - Curr)
            if z_lip > 2.5:
                score += 0.3
                reasons.append("LIP COMPRESSION")
                
            # 4. MICRO-EXPRESSION (Head Jitter)
            z_pitch = get_z(metrics.pitch, "pitch")
            z_yaw = get_z(metrics.yaw, "yaw")
            
            if z_pitch > 3.0 or z_yaw > 3.0:
                 score += 0.3
                 reasons.append("MICRO-TREMOR")
        
        # 5. BLINK RATE (Squinting)
        # If EAR is significantly lower than mean
        z_ear = (self.stats["ear"]["mean"] - metrics.ear) / self.stats["ear"]["std"]
        if z_ear > 3.0:
            score += 0.3
            reasons.append("EYE SQUINT")

        # Cap score
        score = min(score, 1.0)
        
        # Return frame for main loop to draw if needed
        return score, frame, reasons
