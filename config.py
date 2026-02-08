"""
config.py — Central configuration for Dodge the Lasers.

Every tunable parameter lives here so the booth operator can adjust
settings without touching game logic. The difficulty curve, colors,
resolution, and timing are all exposed as simple constants.
"""

# ─── Display ───────────────────────────────────────────────────────
GAME_TITLE = "DODGE THE LASERS"
# Internal resolution for game logic and collision (camera resolution).
INTERNAL_WIDTH = 640
INTERNAL_HEIGHT = 480
# Output display resolution (the TV). PyGame scales internal→display.
DISPLAY_WIDTH = 1920
DISPLAY_HEIGHT = 1080
FULLSCREEN = True      # Set False for development/debugging
TARGET_FPS = 30

# ─── Camera ────────────────────────────────────────────────────────
CAMERA_INDEX = 0                  # 0 = default webcam
CAMERA_MIRROR = True              # Flip horizontally for mirror effect
LOCK_EXPOSURE = False             # Set True at venue after manual tuning
EXPOSURE_VALUE = -6               # Manual exposure (camera-dependent)
# MediaPipe Selfie Segmentation
SEGMENTATION_MODEL = 1            # 0 = general, 1 = landscape (faster)
SEGMENTATION_THRESHOLD = 0.5      # Confidence threshold for body mask
# MediaPipe Pose (optional skeleton overlay)
ENABLE_POSE = False               # Disable to save ~10ms per frame
POSE_COMPLEXITY = 0               # 0 = Lite (fastest)

# ─── Colors (BGR for OpenCV, RGB for PyGame) ───────────────────────
# We store as RGB tuples; camera.py converts to BGR where needed.
COLOR_BACKGROUND = (10, 10, 15)         # Near-black
COLOR_BODY_NEON = (0, 212, 255)         # Electric cyan
COLOR_LASER_HORIZONTAL = (0, 212, 255)  # Cyan
COLOR_LASER_VERTICAL = (255, 0, 110)    # Hot magenta
COLOR_LASER_CROSS_H = (0, 212, 255)     # Cyan (horizontal part)
COLOR_LASER_CROSS_V = (255, 0, 110)     # Magenta (vertical part)
COLOR_LASER_SWEEP = (255, 214, 0)       # Gold
COLOR_LASER_ANKLE_BREAKER = (255, 100, 0)   # Orange (lava)
COLOR_LASER_ANKLE_BRIGHT = (255, 200, 50)   # Bright lava highlights
COLOR_LASER_HEAD_HUNTER = (170, 0, 255)     # Purple
COLOR_LASER_ANTI_CAMP = (255, 30, 30)       # Bright red
COLOR_HIT_FLASH = (255, 0, 0)           # Red
COLOR_HUD_TEXT = (255, 255, 255)        # White
COLOR_HUD_SHADOW = (0, 0, 0)           # Black shadow behind text
COLOR_COUNTDOWN = (255, 255, 255)       # White countdown numbers
COLOR_GAMEOVER = (255, 255, 255)        # White
COLOR_HIGHSCORE = (255, 214, 0)         # Gold for new high score
COLOR_IDLE_TEXT = (0, 212, 255)         # Cyan for attract screen

# Difficulty tier label colors
COLOR_TIER_EASY = (0, 200, 83)         # Green
COLOR_TIER_MEDIUM = (255, 214, 0)      # Yellow
COLOR_TIER_HARD = (255, 109, 0)        # Orange
COLOR_TIER_INSANE = (213, 0, 0)        # Red

# ─── Difficulty Curve ──────────────────────────────────────────────
# All values are functions of T (survival time in seconds).
# spawn_interval = max(MIN_INTERVAL, BASE_INTERVAL - T * INTERVAL_DECAY)
SPAWN_BASE_INTERVAL = 3.5     # Seconds between beams at T=0
SPAWN_MIN_INTERVAL = 1.2      # Fastest spawn rate
SPAWN_INTERVAL_DECAY = 0.015  # Rate of interval decrease per second

# gap_size = max(MIN_GAP, BASE_GAP - T * GAP_SHRINK)
# Expressed as fraction of screen dimension (0.0 to 1.0)
GAP_BASE_SIZE = 0.40
GAP_MIN_SIZE = 0.18
GAP_SHRINK_RATE = 0.002

# warning_time = max(MIN_WARNING, BASE_WARNING - T * WARNING_DECAY)
# During warning the beam position and safe gap are previewed on screen.
WARNING_BASE_MS = 1500         # Milliseconds of warning at T=0
WARNING_MIN_MS = 500
WARNING_DECAY = 7.5            # ms reduction per second of survival

# beam_active = max(MIN_ACTIVE, BASE_ACTIVE - T * ACTIVE_DECAY)
# How long the beam stays on screen (dangerous) after the warning ends.
BEAM_ACTIVE_BASE = 1.8        # Seconds at T=0
BEAM_ACTIVE_MIN = 0.7         # Minimum active duration
BEAM_ACTIVE_DECAY = 0.008     # Seconds lost per second of survival

# Beam type unlock times (seconds of survival)
UNLOCK_ANKLE_BREAKER = 10.0   # Forces jumping early on
UNLOCK_VERTICAL = 15.0
UNLOCK_HEAD_HUNTER = 25.0     # Forces ducking
UNLOCK_CROSS = 30.0

# ─── Ankle Breaker (jump beam) ────────────────────────────────────
ANKLE_BREAKER_HEIGHT = 0.15   # Fraction of screen from bottom (solid, no gap)

# ─── Head Hunter (duck beam) ─────────────────────────────────────
HEAD_HUNTER_HEIGHT = 0.40     # Fraction of screen from top (solid, no gap)

# ─── Anti-Camping ────────────────────────────────────────────────
CAMPING_THRESHOLD = 25        # Pixel movement to reset camp timer
CAMPING_TIME = 3.0            # Seconds stationary before warning reticle appears
CAMPING_WARNING_TIME = 2.0    # Seconds of warning before anti-camp laser fires
ANTI_CAMP_WARNING_MS = 500    # Short beam warning (player already sees reticle)
ANTI_CAMP_ACTIVE_DURATION = 1.5  # How long the anti-camp beam stays active

# ─── Beam Rendering ───────────────────────────────────────────────
BEAM_CORE_WIDTH = 24           # Core beam width in pixels
BEAM_INNER_GLOW = 10           # Extra pixels each side for inner glow
BEAM_OUTER_GLOW = 20           # Extra pixels each side for outer glow
BEAM_INNER_ALPHA = 0.40        # Opacity of inner glow layer
BEAM_OUTER_ALPHA = 0.15        # Opacity of outer glow layer

# ─── Player / Body Rendering ──────────────────────────────────────
BODY_BLUR_KERNEL = 7           # Gaussian blur on mask before Canny
BODY_CANNY_LOW = 50            # Canny edge detection thresholds
BODY_CANNY_HIGH = 150
BODY_DILATE_KERNEL = 3         # Kernel size for edge thickening
BODY_DILATE_ITERATIONS = 1
BODY_GLOW_KERNEL = 21          # Gaussian blur for neon glow halo
BODY_GLOW_INTENSITY = 0.6      # Blend weight of glow layer

# Collision forgiveness: erode body mask before collision check
# Makes the hitbox slightly smaller than the visual silhouette.
COLLISION_ERODE_PX = 5

# ─── Lives & Invincibility ────────────────────────────────────────
STARTING_LIVES = 3
INVINCIBILITY_DURATION = 1.0   # Seconds of invincibility after a hit
INVINCIBILITY_FLASH_HZ = 8    # Flash frequency during invincibility

# ─── Hit Flash ─────────────────────────────────────────────────────
HIT_FLASH_DURATION = 0.2      # Seconds of red screen flash
HIT_FLASH_ALPHA = 40           # Opacity of red overlay (0-255)

# ─── Particles ─────────────────────────────────────────────────────
PARTICLES_ON_HIT = 150         # Particles spawned per collision
PARTICLES_ON_HIGHSCORE = 500   # Particles for new high score celebration
PARTICLE_MAX_COUNT = 2000      # Hard cap on total active particles
PARTICLE_LIFETIME = 0.8        # Seconds before particle fades
PARTICLE_DRAG = 0.96           # Velocity multiplier per frame (friction)
PARTICLE_SPEED_MIN = 2.0       # Min initial speed (pixels/frame)
PARTICLE_SPEED_MAX = 8.0       # Max initial speed
PARTICLE_SIZE_MIN = 2          # Min radius in pixels
PARTICLE_SIZE_MAX = 4          # Max radius

# ─── Countdown ─────────────────────────────────────────────────────
COUNTDOWN_DURATION = 3         # Seconds (3, 2, 1, GO!)

# ─── Game Over ─────────────────────────────────────────────────────
GAMEOVER_DISPLAY_TIME = 5.0    # Seconds before returning to IDLE

# ─── Idle / Attract Screen ────────────────────────────────────────
IDLE_TEXT_MAIN = "STEP INTO THE FRAME"
IDLE_TEXT_SUB = "to play"
IDLE_PULSE_SPEED = 2.0         # Speed of text pulsing animation

# ─── Leaderboard ──────────────────────────────────────────────────
LEADERBOARD_FILE = "leaderboard.json"
LEADERBOARD_MAX_ENTRIES = 10

# ─── Body Detection Thresholds ────────────────────────────────────
# Minimum body pixels to consider "body detected"
BODY_DETECT_MIN_PIXELS = 500
# Frames without body before triggering "STEP CLOSER" hint
BODY_LOST_HINT_FRAMES = 30     # ~1 second at 30fps
# Seconds without body during PLAYING before auto-game-over
BODY_LOST_GAMEOVER_SEC = 5.0

# ─── Mask Cleaning (morphology for noisy segmentation) ────────────
MASK_MORPH_KERNEL = 5          # Kernel size for open/close operations
ENABLE_MASK_CLEANING = True

# ─── Debug ─────────────────────────────────────────────────────────
DEBUG_FPS = False              # Show FPS counter
DEBUG_MASK = False             # Show raw body mask overlay
DEBUG_COLLISION = False        # Highlight collision areas

# ─── Audio ─────────────────────────────────────────────────────────
ENABLE_AUDIO = True
AUDIO_VOLUME = 0.7             # Master volume (0.0 - 1.0)
