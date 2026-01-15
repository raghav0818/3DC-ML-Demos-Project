// Computer Vision Types
export type CVMode = 'clown-nose' | 'rock-paper' | 'victory';

export interface FaceLandmark {
    x: number;
    y: number;
    z: number;
}

export interface HandLandmark {
    x: number;
    y: number;
    z: number;
}

export interface PoseLandmark {
    x: number;
    y: number;
    z: number;
    visibility?: number;
}

export interface CVDetectionResult {
    faceLandmarks?: FaceLandmark[][];
    handLandmarks?: HandLandmark[][];
    poseLandmarks?: PoseLandmark[][];
}

export interface PythonCodeSnippet {
    title: string;
    description: string;
    code: string;
    language: 'python';
}

export const PYTHON_SNIPPETS: Record<CVMode, PythonCodeSnippet> = {
    'clown-nose': {
        title: 'Clown Nose Filter (Python)',
        description: 'Draw a scaled circle on the nose tip using OpenCV and MediaPipe',
        language: 'python',
        code: `import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    min_detection_confidence=0.5
)

# Process frame
rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
results = face_mesh.process(rgb_frame)

if results.multi_face_landmarks:
    for face_landmarks in results.multi_face_landmarks:
        # Get nose tip (landmark #4)
        nose_tip = face_landmarks.landmark[4]
        nose_x = int(nose_tip.x * frame.shape[1])
        nose_y = int(nose_tip.y * frame.shape[0])
        
        # Calculate scale based on face depth
        left_cheek = face_landmarks.landmark[234]
        right_cheek = face_landmarks.landmark[454]
        cheek_distance = abs(right_cheek.x - left_cheek.x)
        radius = int(cheek_distance * frame.shape[1] * 0.15)
        
        # Draw red circle
        cv2.circle(frame, (nose_x, nose_y), radius, (0, 0, 255), -1)
`,
    },
    'rock-paper': {
        title: 'Rock/Paper/Scissors Classifier (Python)',
        description: 'Count extended fingers to classify hand gestures',
        language: 'python',
        code: `import cv2
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7
)

def count_fingers(hand_landmarks):
    """Count extended fingers based on landmark positions"""
    finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
    finger_pips = [6, 10, 14, 18]
    
    extended = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            extended += 1
    
    return extended

# Process frame
results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

if results.multi_hand_landmarks:
    for hand_landmarks in results.multi_hand_landmarks:
        fingers = count_fingers(hand_landmarks)
        
        if fingers <= 1:
            gesture = "ROCK"
            color = (0, 0, 255)  # Red
        elif fingers == 2:
            gesture = "SCISSORS"
            color = (255, 136, 0)  # Blue
        elif fingers >= 4:
            gesture = "PAPER"
            color = (0, 255, 0)  # Green
        else:
            gesture = "UNKNOWN"
            color = (0, 255, 255)  # Yellow
        
        cv2.putText(frame, gesture, (50, 100), 
                    cv2.FONT_HERSHEY_SIMPLEX, 2, color, 3)
`,
    },
    'victory': {
        title: 'Victory Pose Detector (Python)',
        description: 'Detect when both hands are raised above the head',
        language: 'python',
        code: `import cv2
import mediapipe as mp

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Process frame
results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

if results.pose_landmarks:
    landmarks = results.pose_landmarks.landmark
    
    # Get key points
    nose_y = landmarks[0].y
    left_wrist_y = landmarks[15].y
    right_wrist_y = landmarks[16].y
    
    # Check if both wrists are above nose
    if left_wrist_y < nose_y and right_wrist_y < nose_y:
        # Draw gold border
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, h), (0, 215, 255), 10)
        
        # Display "VICTORY!"
        cv2.putText(frame, "VICTORY!", (w//2 - 150, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 215, 255), 5)
        
    # Draw pose landmarks
    mp.solutions.drawing_utils.draw_landmarks(
        frame,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS
    )
`,
    },
};
