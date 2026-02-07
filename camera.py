"""
camera.py — Threaded webcam capture + MediaPipe body segmentation.

Runs as a daemon thread so camera I/O never stalls the game loop.
Writes the latest body_mask (binary numpy array) to a thread-safe
shared buffer.

COMPATIBILITY:
  - MediaPipe >= 0.10.31 (Python 3.13+): uses new Tasks API
    → requires .tflite model file — run setup_model.py first
  - MediaPipe < 0.10.31 with mp.solutions (Python ≤ 3.12): uses legacy API
"""

import threading
import time
import os
import cv2
import numpy as np
import mediapipe as mp

import config as cfg


# ────────────────────────────────────────────────────────────
# Detect which MediaPipe API is available
# ────────────────────────────────────────────────────────────
_USE_TASKS_API = False
try:
    # Try the legacy API first (older mediapipe with mp.solutions)
    _test = mp.solutions.selfie_segmentation
    _USE_TASKS_API = False
    print("[Camera] Using MediaPipe legacy solutions API.")
except AttributeError:
    # Legacy API not available — use the new Tasks API
    _USE_TASKS_API = True
    print("[Camera] Using MediaPipe Tasks API (new).")


class Camera:
    """
    Threaded camera that continuously captures frames, runs MediaPipe
    Selfie Segmentation, and exposes the latest body mask via a
    thread-safe getter.
    """

    def __init__(self):
        # ── Shared state (protected by lock) ──
        self._lock = threading.Lock()
        self._body_mask = np.zeros(
            (cfg.INTERNAL_HEIGHT, cfg.INTERNAL_WIDTH), dtype=np.uint8
        )
        self._body_detected = False
        self._raw_frame = None
        self._running = False

        # ── Initialize the correct MediaPipe backend ──
        if _USE_TASKS_API:
            self._init_tasks_api()
        else:
            self._init_legacy_api()

        # ── Morphology kernel for mask cleaning ──
        self._morph_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (cfg.MASK_MORPH_KERNEL, cfg.MASK_MORPH_KERNEL),
        )

        # ── Erosion kernel for collision forgiveness ──
        ek = cfg.COLLISION_ERODE_PX * 2 + 1
        self._erode_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (ek, ek)
        )

        # ── Frame counter for Tasks API timestamps ──
        self._frame_count = 0

    def _init_tasks_api(self):
        """
        Set up the new MediaPipe Tasks ImageSegmenter.
        Requires a .tflite model file in assets/ — run setup_model.py first.
        """
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python import BaseOptions

        model_path = os.path.join("assets", "selfie_segmenter_landscape.tflite")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"\n[ERROR] Model file not found at '{model_path}'.\n"
                f"Please run 'python setup_model.py' first to download it.\n"
            )

        # VIDEO mode: we call segment_for_video() with monotonic timestamps.
        options = vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            output_confidence_masks=True,
            output_category_mask=False,
            running_mode=vision.RunningMode.VIDEO,
        )
        self._segmenter = vision.ImageSegmenter.create_from_options(options)
        print(f"[Camera] Loaded model: {model_path}")

    def _init_legacy_api(self):
        """Set up the legacy mp.solutions.selfie_segmentation."""
        mp_selfie = mp.solutions.selfie_segmentation
        self._segmenter = mp_selfie.SelfieSegmentation(
            model_selection=cfg.SEGMENTATION_MODEL
        )

    # ────────────────────────────────────────────────────────────
    # Public API (called from main thread)
    # ────────────────────────────────────────────────────────────

    def start(self):
        """Launch the capture thread."""
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Signal the capture thread to stop."""
        self._running = False

    def get_body_mask(self):
        """
        Return the latest body mask (binary uint8, same size as internal
        resolution) and a boolean indicating whether a body was detected.
        """
        with self._lock:
            return self._body_mask.copy(), self._body_detected

    def get_collision_mask(self):
        """
        Return an eroded version of the body mask for collision detection.
        The erosion makes the hitbox slightly smaller than the visual
        silhouette, which feels more forgiving to the player.
        """
        with self._lock:
            mask = self._body_mask.copy()
        if cfg.COLLISION_ERODE_PX > 0:
            mask = cv2.erode(mask, self._erode_kernel, iterations=1)
        return mask

    def get_raw_frame(self):
        """Return the latest raw BGR camera frame (for debug overlay)."""
        with self._lock:
            return self._raw_frame.copy() if self._raw_frame is not None else None

    # ────────────────────────────────────────────────────────────
    # Capture loop (runs in daemon thread)
    # ────────────────────────────────────────────────────────────

    def _capture_loop(self):
        """
        Continuously capture frames from the webcam, run MediaPipe,
        and write results to the shared buffer.
        """
        cap = cv2.VideoCapture(cfg.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.INTERNAL_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.INTERNAL_HEIGHT)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if cfg.LOCK_EXPOSURE:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            cap.set(cv2.CAP_PROP_EXPOSURE, cfg.EXPOSURE_VALUE)

        while self._running:
            ret, frame = cap.read()
            if not ret:
                # Camera disconnected — wait and retry
                time.sleep(0.5)
                cap.release()
                cap = cv2.VideoCapture(cfg.CAMERA_INDEX)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.INTERNAL_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.INTERNAL_HEIGHT)
                continue

            if cfg.CAMERA_MIRROR:
                frame = cv2.flip(frame, 1)

            h, w = frame.shape[:2]
            if w != cfg.INTERNAL_WIDTH or h != cfg.INTERNAL_HEIGHT:
                frame = cv2.resize(frame, (cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT))

            # ── Run segmentation ──
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if _USE_TASKS_API:
                binary_mask = self._process_tasks_api(frame_rgb)
            else:
                binary_mask = self._process_legacy_api(frame_rgb)

            # Fallback to empty mask on failure
            if binary_mask is None:
                binary_mask = np.zeros(
                    (cfg.INTERNAL_HEIGHT, cfg.INTERNAL_WIDTH), dtype=np.uint8
                )

            # ── Clean noisy edges with morphology ──
            if cfg.ENABLE_MASK_CLEANING:
                binary_mask = cv2.morphologyEx(
                    binary_mask, cv2.MORPH_OPEN, self._morph_kernel
                )
                binary_mask = cv2.morphologyEx(
                    binary_mask, cv2.MORPH_CLOSE, self._morph_kernel
                )

            body_detected = np.count_nonzero(binary_mask) > cfg.BODY_DETECT_MIN_PIXELS

            # ── Write to shared buffer ──
            with self._lock:
                self._body_mask = binary_mask
                self._body_detected = body_detected
                self._raw_frame = frame

        # Cleanup
        cap.release()
        try:
            self._segmenter.close()
        except Exception:
            pass

    def _process_tasks_api(self, frame_rgb):
        """
        Process a frame using the new MediaPipe Tasks ImageSegmenter.
        The selfie segmenter model outputs confidence masks where
        high values (close to 1.0) indicate a person.
        Returns a binary uint8 mask (0 or 255).
        """
        try:
            # Tasks API needs a mediapipe.Image and a monotonic timestamp
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=np.ascontiguousarray(frame_rgb),
            )

            self._frame_count += 1
            timestamp_ms = int(self._frame_count * (1000 / cfg.TARGET_FPS))

            result = self._segmenter.segment_for_video(mp_image, timestamp_ms)

            if result.confidence_masks:
                # The selfie_segmenter_landscape model outputs confidence
                # masks. For the binary selfie model there's typically one
                # mask at index 0 (person confidence).
                # If multi-output: index 0 = background, index 1 = person.
                if len(result.confidence_masks) == 1:
                    raw_mask = result.confidence_masks[0].numpy_view()
                else:
                    # Multi-class: last index is typically person
                    raw_mask = result.confidence_masks[-1].numpy_view()

                binary = (raw_mask > cfg.SEGMENTATION_THRESHOLD).astype(np.uint8) * 255

                # Resize to internal resolution if model output differs
                mh, mw = binary.shape[:2]
                if mw != cfg.INTERNAL_WIDTH or mh != cfg.INTERNAL_HEIGHT:
                    binary = cv2.resize(
                        binary,
                        (cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT),
                        interpolation=cv2.INTER_NEAREST,
                    )
                return binary

        except Exception as e:
            # Log infrequently to avoid spamming console
            if self._frame_count % 300 == 1:
                print(f"[Camera] Tasks API error: {e}")

        return None

    def _process_legacy_api(self, frame_rgb):
        """
        Process a frame using the legacy mp.solutions.selfie_segmentation.
        Returns a binary uint8 mask (0 or 255).
        """
        try:
            frame_rgb.flags.writeable = False
            seg_result = self._segmenter.process(frame_rgb)
            frame_rgb.flags.writeable = True

            raw_mask = seg_result.segmentation_mask  # float32 [0,1]
            binary = (raw_mask > cfg.SEGMENTATION_THRESHOLD).astype(np.uint8) * 255

            mh, mw = binary.shape[:2]
            if mw != cfg.INTERNAL_WIDTH or mh != cfg.INTERNAL_HEIGHT:
                binary = cv2.resize(
                    binary,
                    (cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT),
                    interpolation=cv2.INTER_NEAREST,
                )
            return binary

        except Exception as e:
            if self._frame_count % 300 == 1:
                print(f"[Camera] Legacy API error: {e}")

        return None
