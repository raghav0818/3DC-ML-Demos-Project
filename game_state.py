"""
game_state.py — Game state machine.

States: IDLE → COUNTDOWN → PLAYING → HIT → GAME_OVER → (back to IDLE)
Also: PAUSED (operator toggle).

Each state stores when it was entered so time-based transitions
(countdown timer, game-over display, invincibility) can be computed
from a single reference point.
"""

import time
from enum import Enum, auto

import config as cfg


class State(Enum):
    IDLE = auto()       # Attract screen, waiting for a player
    COUNTDOWN = auto()  # 3-2-1 before gameplay starts
    PLAYING = auto()    # Active gameplay
    HIT = auto()        # Brief invincibility after collision
    GAME_OVER = auto()  # Score display, then fade to IDLE
    PAUSED = auto()     # Operator pause


class GameState:
    """
    Manages the current state, transitions, and per-state timing.

    The main game loop calls update() once per frame, passing in
    whether a body is currently detected.  GameState decides when
    to transition and exposes properties that the rest of the game
    (laser spawning, HUD, renderer) can read.
    """

    def __init__(self):
        self.state = State.IDLE
        self._entered_at = time.time()    # When current state was entered

        # Gameplay tracking
        self.lives = cfg.STARTING_LIVES
        self.survival_time = 0.0          # Seconds survived in PLAYING state
        self.play_start_time = 0.0        # Absolute time when PLAYING began
        self.is_invincible = False
        self._invincible_until = 0.0

        # Body tracking for "lost body" detection
        self._body_lost_since = None      # Time when body was last lost
        self._body_lost_frames = 0        # Consecutive frames without body

        # Game-over result (set when entering GAME_OVER)
        self.final_time = 0.0
        self.is_new_highscore = False
        self.leaderboard_rank = -1

        # Pause: remember what state we were in before pausing
        self._paused_from = None

        # Force-difficulty override (keys 1-4 for operator)
        self.forced_difficulty = None      # None = auto, 1-4 = forced tier

        # ── Anti-camping centroid tracking ──
        self._centroid_x = None           # Smoothed centroid X
        self._centroid_y = None           # Smoothed centroid Y
        self._camp_start_time = None      # When the player started staying still
        self.camp_warning_active = False  # True when reticle should be shown
        self.camp_target_x = 0           # X position for the reticle / laser
        self.camp_target_y = 0           # Y position for the reticle

    # ────────────────────────────────────────────────────────────
    # Properties
    # ────────────────────────────────────────────────────────────

    @property
    def time_in_state(self):
        """Seconds since we entered the current state."""
        return time.time() - self._entered_at

    @property
    def countdown_number(self):
        """
        During COUNTDOWN state, returns the number to display (3, 2, 1)
        or 0 when countdown is finished.
        """
        if self.state != State.COUNTDOWN:
            return 0
        elapsed = self.time_in_state
        remaining = cfg.COUNTDOWN_DURATION - elapsed
        if remaining <= 0:
            return 0
        return int(remaining) + 1  # ceil: 2.9→3, 1.1→2, 0.5→1

    @property
    def difficulty_tier(self):
        """
        Return a string label and color for the current difficulty,
        based on survival time T.  Used by the HUD.
        """
        if self.forced_difficulty is not None:
            tiers = [
                ("EASY", cfg.COLOR_TIER_EASY),
                ("MEDIUM", cfg.COLOR_TIER_MEDIUM),
                ("HARD", cfg.COLOR_TIER_HARD),
                ("INSANE", cfg.COLOR_TIER_INSANE),
            ]
            idx = max(0, min(3, self.forced_difficulty - 1))
            return tiers[idx]

        T = self.survival_time
        if T < 15:
            return ("EASY", cfg.COLOR_TIER_EASY)
        elif T < 30:
            return ("MEDIUM", cfg.COLOR_TIER_MEDIUM)
        elif T < 60:
            return ("HARD", cfg.COLOR_TIER_HARD)
        else:
            return ("INSANE", cfg.COLOR_TIER_INSANE)

    # ────────────────────────────────────────────────────────────
    # State transitions
    # ────────────────────────────────────────────────────────────

    def _enter(self, new_state):
        """Transition to a new state and record the entry time."""
        self.state = new_state
        self._entered_at = time.time()

    def update(self, body_detected):
        """
        Called once per frame by the main game loop.
        Handles all automatic state transitions.
        """
        now = time.time()

        # ── Invincibility expiry (runs in any state) ──
        if self.is_invincible and now >= self._invincible_until:
            self.is_invincible = False

        # ── State-specific logic ──
        if self.state == State.IDLE:
            # Waiting for a player to step into frame
            if body_detected:
                self._start_countdown()

        elif self.state == State.COUNTDOWN:
            # Counting down 3-2-1
            if self.time_in_state >= cfg.COUNTDOWN_DURATION:
                self._start_playing()
            # If body disappears during countdown, abort back to idle
            if not body_detected:
                self._body_lost_frames += 1
                if self._body_lost_frames > cfg.BODY_LOST_HINT_FRAMES:
                    self._enter(State.IDLE)
            else:
                self._body_lost_frames = 0

        elif self.state == State.PLAYING:
            # Update survival timer
            self.survival_time = now - self.play_start_time

            # Track body presence
            if not body_detected:
                if self._body_lost_since is None:
                    self._body_lost_since = now
                elif now - self._body_lost_since > cfg.BODY_LOST_GAMEOVER_SEC:
                    # Body lost too long — graceful game over
                    self._trigger_game_over()
            else:
                self._body_lost_since = None

        elif self.state == State.HIT:
            # HIT is a visual sub-state; gameplay continues.
            # We transition back to PLAYING after the flash.
            # (HIT state is really just PLAYING + invincible,
            #  but separated for clarity in the state machine.)
            self.survival_time = now - self.play_start_time
            if self.time_in_state >= cfg.HIT_FLASH_DURATION:
                self._enter(State.PLAYING)

        elif self.state == State.GAME_OVER:
            # Wait, then return to idle
            if self.time_in_state >= cfg.GAMEOVER_DISPLAY_TIME:
                self._enter(State.IDLE)

        elif self.state == State.PAUSED:
            pass  # Do nothing; operator un-pauses manually

    # ────────────────────────────────────────────────────────────
    # Actions (called by main loop on specific events)
    # ────────────────────────────────────────────────────────────

    def register_hit(self):
        """
        Called when collision is detected.  Decrements lives, starts
        invincibility, and either enters HIT state or GAME_OVER.
        Returns True if the player is still alive, False if game over.
        """
        if self.is_invincible:
            return True  # Ignore hits during invincibility

        self.lives -= 1
        self.is_invincible = True
        self._invincible_until = time.time() + cfg.INVINCIBILITY_DURATION

        if self.lives <= 0:
            self._trigger_game_over()
            return False
        else:
            self._enter(State.HIT)
            return True

    def toggle_pause(self):
        """Operator presses P to toggle pause."""
        if self.state == State.PAUSED:
            # Resume to the state we paused from
            if self._paused_from is not None:
                self.state = self._paused_from
                self._paused_from = None
                # Adjust timers to account for pause duration
                # (simplified: we just resume, accepting minor time drift)
        else:
            self._paused_from = self.state
            self.state = State.PAUSED

    def set_game_over_result(self, rank, is_highscore):
        """Called by main loop after leaderboard insertion."""
        self.leaderboard_rank = rank
        self.is_new_highscore = is_highscore

    # ────────────────────────────────────────────────────────────
    # Anti-camping centroid tracking
    # ────────────────────────────────────────────────────────────

    def update_centroid(self, cx, cy):
        """
        Update the player's centroid and detect camping.

        Called every frame from main.py with the body mask centroid.
        Pass (None, None) when no body is detected.
        """
        if self.state not in (State.PLAYING, State.HIT):
            self._reset_camping()
            return

        if cx is None or cy is None:
            return

        # First frame: just store the initial position
        if self._centroid_x is None:
            self._centroid_x = float(cx)
            self._centroid_y = float(cy)
            return

        # Check movement distance from the smoothed reference
        dx = cx - self._centroid_x
        dy = cy - self._centroid_y
        distance = (dx * dx + dy * dy) ** 0.5

        if distance > cfg.CAMPING_THRESHOLD:
            # Player moved enough — reset camping
            self._centroid_x = float(cx)
            self._centroid_y = float(cy)
            self._camp_start_time = None
            self.camp_warning_active = False
        else:
            # Player is stationary — start/continue camp timer
            now = time.time()
            if self._camp_start_time is None:
                self._camp_start_time = now

            camp_duration = now - self._camp_start_time
            if camp_duration >= cfg.CAMPING_TIME:
                self.camp_warning_active = True
                self.camp_target_x = int(self._centroid_x)
                self.camp_target_y = int(self._centroid_y)

            # Smooth the reference to handle body segmentation noise
            self._centroid_x = self._centroid_x * 0.95 + cx * 0.05
            self._centroid_y = self._centroid_y * 0.95 + cy * 0.05

    def consume_camp_laser(self):
        """
        Check if the anti-camp laser should fire.

        Returns the target X coordinate when it's time to fire,
        or None if not yet. Resets camping state after firing
        so the detection cycle starts fresh.
        """
        if not self.camp_warning_active or self._camp_start_time is None:
            return None

        now = time.time()
        total_camp = now - self._camp_start_time
        if total_camp >= cfg.CAMPING_TIME + cfg.CAMPING_WARNING_TIME:
            target_x = self.camp_target_x
            # Reset so the cycle can trigger again
            self._camp_start_time = None
            self.camp_warning_active = False
            return target_x

        return None

    def _reset_camping(self):
        """Clear all camping tracking state."""
        self._centroid_x = None
        self._centroid_y = None
        self._camp_start_time = None
        self.camp_warning_active = False

    # ────────────────────────────────────────────────────────────
    # Internal helpers
    # ────────────────────────────────────────────────────────────

    def _start_countdown(self):
        """Reset everything and begin the countdown."""
        self.lives = cfg.STARTING_LIVES
        self.survival_time = 0.0
        self.is_invincible = False
        self.final_time = 0.0
        self.is_new_highscore = False
        self.leaderboard_rank = -1
        self._body_lost_since = None
        self._body_lost_frames = 0
        self.forced_difficulty = None
        self._reset_camping()
        self._enter(State.COUNTDOWN)

    def _start_playing(self):
        """Countdown finished — begin actual gameplay."""
        self.play_start_time = time.time()
        self.survival_time = 0.0
        self._enter(State.PLAYING)

    def _trigger_game_over(self):
        """End the game and record the final time."""
        self.final_time = self.survival_time
        self.is_invincible = False
        self._enter(State.GAME_OVER)
