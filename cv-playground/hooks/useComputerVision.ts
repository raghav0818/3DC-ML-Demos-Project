import { useEffect, useRef, useState, useCallback } from 'react';
import { FilesetResolver, FaceLandmarker, HandLandmarker, PoseLandmarker } from '@mediapipe/tasks-vision';
import type { CVMode } from '@/types/cv';

interface UseComputerVisionOptions {
    mode: CVMode;
    videoElement: HTMLVideoElement | null;
    canvasElement: HTMLCanvasElement | null;
    enabled: boolean;
}

interface UseComputerVisionReturn {
    isLoading: boolean;
    error: string | null;
    fps: number;
}

export function useComputerVision({
    mode,
    videoElement,
    canvasElement,
    enabled,
}: UseComputerVisionOptions): UseComputerVisionReturn {
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [fps, setFps] = useState(0);

    const faceLandmarkerRef = useRef<FaceLandmarker | null>(null);
    const handLandmarkerRef = useRef<HandLandmarker | null>(null);
    const poseLandmarkerRef = useRef<PoseLandmarker | null>(null);

    const animationFrameRef = useRef<number>();
    const lastTimeRef = useRef<number>(0);
    const frameCountRef = useRef<number>(0);
    const fpsTimeRef = useRef<number>(0);

    // Initialize MediaPipe models
    useEffect(() => {
        let isMounted = true;

        async function initializeModels() {
            try {
                setIsLoading(true);
                setError(null);

                const vision = await FilesetResolver.forVisionTasks(
                    'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
                );

                if (!isMounted) return;

                // Initialize all models
                const [faceLandmarker, handLandmarker, poseLandmarker] = await Promise.all([
                    FaceLandmarker.createFromOptions(vision, {
                        baseOptions: {
                            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
                            delegate: 'GPU',
                        },
                        numFaces: 1,
                        runningMode: 'VIDEO',
                        minFaceDetectionConfidence: 0.5,
                        minFacePresenceConfidence: 0.5,
                        minTrackingConfidence: 0.5,
                    }),
                    HandLandmarker.createFromOptions(vision, {
                        baseOptions: {
                            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
                            delegate: 'GPU',
                        },
                        numHands: 2,
                        runningMode: 'VIDEO',
                        minHandDetectionConfidence: 0.5,
                        minHandPresenceConfidence: 0.5,
                        minTrackingConfidence: 0.5,
                    }),
                    PoseLandmarker.createFromOptions(vision, {
                        baseOptions: {
                            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
                            delegate: 'GPU',
                        },
                        runningMode: 'VIDEO',
                        numPoses: 1,
                        minPoseDetectionConfidence: 0.5,
                        minPosePresenceConfidence: 0.5,
                        minTrackingConfidence: 0.5,
                    }),
                ]);

                if (isMounted) {
                    faceLandmarkerRef.current = faceLandmarker;
                    handLandmarkerRef.current = handLandmarker;
                    poseLandmarkerRef.current = poseLandmarker;
                    setIsLoading(false);
                }
            } catch (err) {
                if (isMounted) {
                    setError(err instanceof Error ? err.message : 'Failed to load CV models');
                    setIsLoading(false);
                }
            }
        }

        initializeModels();

        return () => {
            isMounted = false;
        };
    }, []);

    // Main processing loop
    const processFrame = useCallback((timestamp: number) => {
        if (!enabled || !videoElement || !canvasElement || isLoading) {
            animationFrameRef.current = requestAnimationFrame(processFrame);
            return;
        }

        const ctx = canvasElement.getContext('2d');
        if (!ctx) return;

        // Calculate FPS
        frameCountRef.current++;
        if (!fpsTimeRef.current) fpsTimeRef.current = timestamp;
        const elapsed = timestamp - fpsTimeRef.current;
        if (elapsed >= 1000) {
            setFps(Math.round((frameCountRef.current * 1000) / elapsed));
            frameCountRef.current = 0;
            fpsTimeRef.current = timestamp;
        }

        // Clear canvas
        ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);

        try {
            const currentTime = performance.now();

            // Process based on mode
            switch (mode) {
                case 'clown-nose':
                    if (faceLandmarkerRef.current && videoElement.readyState >= 2) {
                        const results = faceLandmarkerRef.current.detectForVideo(videoElement, currentTime);
                        drawClownNose(ctx, results, canvasElement.width, canvasElement.height);
                    }
                    break;

                case 'rock-paper':
                    if (handLandmarkerRef.current && videoElement.readyState >= 2) {
                        const results = handLandmarkerRef.current.detectForVideo(videoElement, currentTime);
                        drawRockPaper(ctx, results, canvasElement.width, canvasElement.height);
                    }
                    break;

                case 'victory':
                    if (poseLandmarkerRef.current && videoElement.readyState >= 2) {
                        const results = poseLandmarkerRef.current.detectForVideo(videoElement, currentTime);
                        drawVictory(ctx, results, canvasElement.width, canvasElement.height);
                    }
                    break;
            }
        } catch (err) {
            console.error('Frame processing error:', err);
        }

        lastTimeRef.current = timestamp;
        animationFrameRef.current = requestAnimationFrame(processFrame);
    }, [mode, videoElement, canvasElement, enabled, isLoading]);

    // Start/stop animation loop
    useEffect(() => {
        if (enabled && !isLoading) {
            animationFrameRef.current = requestAnimationFrame(processFrame);
        }

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [enabled, isLoading, processFrame]);

    return { isLoading, error, fps };
}

// Drawing functions
function drawClownNose(
    ctx: CanvasRenderingContext2D,
    results: any,
    width: number,
    height: number
) {
    if (!results.faceLandmarks || results.faceLandmarks.length === 0) return;

    const landmarks = results.faceLandmarks[0];

    // Get nose tip (landmark 4)
    const noseTip = landmarks[4];
    const noseX = noseTip.x * width;
    const noseY = noseTip.y * height;

    // Calculate scale based on cheekbone distance
    const leftCheek = landmarks[234];
    const rightCheek = landmarks[454];
    const cheekDistance = Math.sqrt(
        Math.pow((rightCheek.x - leftCheek.x) * width, 2) +
        Math.pow((rightCheek.y - leftCheek.y) * height, 2)
    );

    const radius = Math.max(10, Math.min(cheekDistance * 0.15, 80));

    // Draw red clown nose
    ctx.fillStyle = '#FF0000';
    ctx.beginPath();
    ctx.arc(noseX, noseY, radius, 0, 2 * Math.PI);
    ctx.fill();

    // Add highlight for 3D effect
    const highlightOffset = radius * 0.3;
    const highlightRadius = radius * 0.3;
    ctx.fillStyle = 'rgba(255, 100, 100, 0.6)';
    ctx.beginPath();
    ctx.arc(noseX - highlightOffset, noseY - highlightOffset, highlightRadius, 0, 2 * Math.PI);
    ctx.fill();

    // Draw minimal face landmarks
    ctx.fillStyle = '#00FF00';
    [4, 1, 234, 454, 10, 152].forEach((idx) => {
        if (landmarks[idx]) {
            const lm = landmarks[idx];
            ctx.beginPath();
            ctx.arc(lm.x * width, lm.y * height, 3, 0, 2 * Math.PI);
            ctx.fill();
        }
    });
}

function drawRockPaper(
    ctx: CanvasRenderingContext2D,
    results: any,
    width: number,
    height: number
) {
    if (!results.landmarks || results.landmarks.length === 0) {
        // No hand detected
        // Save context and flip for text
        ctx.save();
        ctx.scale(-1, 1);
        ctx.fillStyle = '#00FFFF';
        ctx.font = 'bold 32px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Show your hand!', -width / 2, height / 2);
        ctx.restore();
        return;
    }

    const landmarks = results.landmarks[0];

    // Draw hand connections
    const HAND_CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4],  // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],  // Index
        [0, 9], [9, 10], [10, 11], [11, 12],  // Middle
        [0, 13], [13, 14], [14, 15], [15, 16],  // Ring
        [0, 17], [17, 18], [18, 19], [19, 20],  // Pinky
        [5, 9], [9, 13], [13, 17]  // Palm
    ];

    ctx.strokeStyle = '#00FF00';
    ctx.lineWidth = 2;
    HAND_CONNECTIONS.forEach(([start, end]) => {
        const startLm = landmarks[start];
        const endLm = landmarks[end];
        ctx.beginPath();
        ctx.moveTo(startLm.x * width, startLm.y * height);
        ctx.lineTo(endLm.x * width, endLm.y * height);
        ctx.stroke();
    });

    // Draw landmarks
    ctx.fillStyle = '#FF00FF';
    landmarks.forEach((lm: any) => {
        ctx.beginPath();
        ctx.arc(lm.x * width, lm.y * height, 5, 0, 2 * Math.PI);
        ctx.fill();
    });

    // Detect specific finger states
    const indexExtended = landmarks[8].y < landmarks[6].y;
    const middleExtended = landmarks[12].y < landmarks[10].y;
    const ringExtended = landmarks[16].y < landmarks[14].y;
    const pinkyExtended = landmarks[20].y < landmarks[18].y;

    // Check thumb (horizontal distance from wrist)
    const wrist = landmarks[0];
    const thumbTip = landmarks[4];
    const thumbPip = landmarks[3];
    const thumbExtended = Math.abs(thumbTip.x - wrist.x) > Math.abs(thumbPip.x - wrist.x);

    // Count total extended fingers
    let extendedCount = 0;
    if (indexExtended) extendedCount++;
    if (middleExtended) extendedCount++;
    if (ringExtended) extendedCount++;
    if (pinkyExtended) extendedCount++;
    if (thumbExtended) extendedCount++;

    // Classify gesture with specific scissors logic
    let gesture = '';
    let color = '';
    let bgColor = '';

    // SCISSORS: Index + Middle extended, Ring + Pinky NOT extended
    if (indexExtended && middleExtended && !ringExtended && !pinkyExtended) {
        gesture = 'SCISSORS';
        color = '#0088FF';  // Blue
        bgColor = 'rgba(0, 136, 255, 0.3)';
    }
    // ROCK: 0 or 1 finger extended
    else if (extendedCount <= 1) {
        gesture = 'ROCK';
        color = '#FF0000';  // Red
        bgColor = 'rgba(255, 0, 0, 0.3)';
    }
    // PAPER: ALL 5 fingers extended (including thumb)
    else if (extendedCount === 5) {
        gesture = 'PAPER';
        color = '#00FF00';  // Green
        bgColor = 'rgba(0, 255, 0, 0.3)';
    }
    // Unknown gesture
    else {
        gesture = `??? (${extendedCount})`;
        color = '#FFFF00';  // Yellow
        bgColor = 'rgba(255, 255, 0, 0.3)';
    }

    // Get hand center
    const centerX = landmarks[9].x * width;
    const centerY = landmarks[9].y * height - 60;

    // Save context for text flipping
    ctx.save();
    ctx.scale(-1, 1);

    // Draw background
    ctx.font = 'bold 48px Inter, sans-serif';
    const metrics = ctx.measureText(gesture);
    const textWidth = metrics.width;
    const textHeight = 60;

    ctx.fillStyle = bgColor;
    ctx.fillRect(
        -centerX - textWidth / 2 - 20,
        centerY - textHeight,
        textWidth + 40,
        textHeight + 20
    );

    // Draw text
    ctx.fillStyle = color;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(gesture, -centerX, centerY - textHeight / 2);

    // Draw finger count
    ctx.font = '20px Inter, sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.textAlign = 'right';
    ctx.fillText(`Fingers: ${extendedCount}`, -10, height - 20);

    ctx.restore();
}

function drawVictory(
    ctx: CanvasRenderingContext2D,
    results: any,
    width: number,
    height: number
) {
    if (!results.landmarks || results.landmarks.length === 0) {
        // Save context and flip for text
        ctx.save();
        ctx.scale(-1, 1);
        ctx.fillStyle = '#00FFFF';
        ctx.font = 'bold 24px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Stand back so full body is visible', -width / 2, height / 2);
        ctx.restore();
        return;
    }

    const landmarks = results.landmarks[0];

    // Draw pose connections (simplified)
    const POSE_CONNECTIONS = [
        [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],  // Arms
        [11, 23], [12, 24], [23, 24],  // Torso
        [23, 25], [25, 27], [24, 26], [26, 28],  // Legs
    ];

    ctx.strokeStyle = '#00FFFF';
    ctx.lineWidth = 3;
    POSE_CONNECTIONS.forEach(([start, end]) => {
        if (landmarks[start] && landmarks[end]) {
            const startLm = landmarks[start];
            const endLm = landmarks[end];
            ctx.beginPath();
            ctx.moveTo(startLm.x * width, startLm.y * height);
            ctx.lineTo(endLm.x * width, endLm.y * height);
            ctx.stroke();
        }
    });

    // Draw landmarks
    landmarks.forEach((lm: any, idx: number) => {
        // Color code: face=cyan, arms=green, legs=magenta
        if (idx < 11) ctx.fillStyle = '#00FFFF';
        else if (idx < 17) ctx.fillStyle = '#00FF00';
        else ctx.fillStyle = '#FF00FF';

        ctx.beginPath();
        ctx.arc(lm.x * width, lm.y * height, 6, 0, 2 * Math.PI);
        ctx.fill();
    });

    // Check victory pose
    const nose = landmarks[0];
    const leftWrist = landmarks[15];
    const rightWrist = landmarks[16];

    const isVictory = leftWrist.y < nose.y && rightWrist.y < nose.y;

    if (isVictory) {
        // Draw gold border with glow effect
        ctx.strokeStyle = '#FFD700';
        ctx.lineWidth = 15;
        ctx.shadowBlur = 30;
        ctx.shadowColor = '#FFD700';
        ctx.strokeRect(10, 10, width - 20, height - 20);
        ctx.shadowBlur = 0;

        // Draw VICTORY text (flipped for readability)
        ctx.save();
        ctx.scale(-1, 1);
        ctx.font = 'bold 80px Inter, sans-serif';
        ctx.fillStyle = '#FFD700';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowBlur = 20;
        ctx.shadowColor = '#FFD700';
        ctx.fillText('VICTORY!', -width / 2, height / 2);
        ctx.shadowBlur = 0;
        ctx.restore();
    }

    // Draw wrist indicators with flipped text
    ctx.fillStyle = '#FF00FF';
    ctx.beginPath();
    ctx.arc(leftWrist.x * width, leftWrist.y * height, 15, 0, 2 * Math.PI);
    ctx.fill();

    ctx.save();
    ctx.scale(-1, 1);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 16px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('L', -leftWrist.x * width, leftWrist.y * height + 5);

    ctx.fillStyle = '#FF00FF';
    ctx.beginPath();
    ctx.arc(-rightWrist.x * width, rightWrist.y * height, 15, 0, 2 * Math.PI);
    ctx.fill();

    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('R', -rightWrist.x * width, rightWrist.y * height + 5);

    // Instructions
    ctx.fillStyle = '#CCCCCC';
    ctx.font = '18px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('Raise both hands above your head!', -10, height - 20);
    ctx.restore();
}
