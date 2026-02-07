# DODGE THE LASERS ⚡

**Full-body interactive laser dodge game for SUTD Open House 2026**

Stand in front of the screen. See yourself as a glowing neon silhouette. Dodge laser beams that get faster and faster until you can't — then try to beat the high score.

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the AI model (one-time, ~250KB)
python setup_model.py

# 5. Run the game
python main.py
```

> **Python 3.13 users:** Step 4 is **required**. The game uses MediaPipe's new Tasks API which needs a separate model file. The setup script downloads it automatically.

## Operator Controls

| Key | Action |
|-----|--------|
| **Escape** | Exit the application |
| **P** | Pause / Unpause |
| **Ctrl+R** | Reset the leaderboard |
| **F** | Toggle FPS counter |
| **D** | Toggle debug mask view |
| **1-4** | Force difficulty tier (for testing) |
| **0** | Reset difficulty to auto |

## Configuration

All tunable settings (colors, difficulty curve, resolution, camera index) are in **`config.py`**. Key settings to check before the event:

- `CAMERA_INDEX` — Change if using an external webcam (try `1` if `0` doesn't work)
- `FULLSCREEN` — Set to `False` during development, `True` at the venue
- `DISPLAY_WIDTH` / `DISPLAY_HEIGHT` — Match your TV resolution
- `STARTING_LIVES` — Default is 3. Increase to 5 if games are too short.
- Difficulty curve constants — Adjust if games are too easy or hard after playtesting

## Venue Setup Checklist

1. **Lighting**: Test segmentation quality. Bring a USB LED panel if needed.
2. **Camera**: Use a Logitech C920/C930e if available. Position at chest height (~1.2m).
3. **Display**: Connect HDMI to TV. Verify fullscreen mode works.
4. **Play Area**: Clear a 2m × 2m space. Mark with tape on the floor.
5. **Power**: Plug in laptop. Disable sleep/dimming. Set High Performance power plan.
6. **Audio**: Connect external speaker if available (optional).

## Project Structure

```
dodge_the_lasers/
├── main.py              # Entry point — game loop
├── config.py            # All tunable constants
├── camera.py            # Threaded webcam + MediaPipe (Tasks + legacy)
├── setup_model.py       # One-time model download script
├── game_state.py        # State machine (IDLE→COUNTDOWN→PLAYING→GAME_OVER)
├── laser.py             # Laser beam system + collision masks
├── player.py            # Neon body silhouette rendering
├── particles.py         # NumPy-vectorized particle effects
├── hud.py               # HUD, countdown, game-over, attract screen
├── leaderboard.py       # Persistent JSON leaderboard
├── requirements.txt     # Python dependencies
├── leaderboard.json     # Auto-generated score file
└── assets/
    └── selfie_segmenter_landscape.tflite  # Downloaded by setup_model.py
```

## Troubleshooting

**Camera not detected**: Try changing `CAMERA_INDEX` in config.py to `1` or `2`.

**Low FPS**: Set `ENABLE_POSE = False` in config.py (saves ~10ms/frame). Reduce `DISPLAY_WIDTH`/`DISPLAY_HEIGHT`.

**Body not detected well**: Improve lighting. Set `LOCK_EXPOSURE = True` and tune `EXPOSURE_VALUE`. Ensure background behind player is relatively uniform.

**Game crashes**: Check `crash.log` for details. The game auto-logs all crashes. Restart with `python main.py`.
