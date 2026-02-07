"""
main.py — Entry point for Dodge the Lasers.

This file initializes PyGame, starts the camera thread, and runs the
main game loop.  The loop follows the exact 8-step pipeline described
in the PRD:

  1. Read body_mask from shared camera buffer (non-blocking)
  2. Update game state machine
  3. Spawn new lasers based on difficulty curve
  4. Update laser positions
  5. Collision detection: np.any(body_mask & laser_mask)
  6. Update particle systems
  7. Render frame (clear → lasers → body → particles → HUD)
  8. Flip display buffer, enforce frame rate

Operator controls:
  Escape  — Exit
  P       — Toggle pause
  Ctrl+R  — Reset leaderboard
  F       — Toggle FPS counter
  D       — Toggle debug mask view
  1-4     — Force difficulty tier
"""

import sys
import time

import numpy as np
import pygame

import config as cfg
from camera import Camera
from game_state import GameState, State
from laser import LaserManager
from particles import ParticleSystem
from player import PlayerRenderer
from hud import HUD
from leaderboard import Leaderboard


def main():
    # ══════════════════════════════════════════════════════════════
    # INITIALIZATION
    # ══════════════════════════════════════════════════════════════

    pygame.init()
    pygame.mixer.init()

    # ── Display setup ──
    # We render everything at internal resolution (640×480) onto an
    # off-screen surface, then scale it up to the display resolution
    # (1920×1080 or whatever the TV supports).  This keeps all game
    # logic and collision detection at a fixed, predictable resolution.

    if cfg.FULLSCREEN:
        display = pygame.display.set_mode(
            (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF,
        )
    else:
        display = pygame.display.set_mode(
            (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT),
            pygame.HWSURFACE | pygame.DOUBLEBUF,
        )

    pygame.display.set_caption(cfg.GAME_TITLE)
    pygame.mouse.set_visible(False)

    # Internal render surface (all game logic happens at this resolution)
    game_surface = pygame.Surface(
        (cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT), pygame.SRCALPHA
    )

    clock = pygame.time.Clock()

    # ── Initialize all game modules ──
    camera = Camera()
    game_state = GameState()
    laser_mgr = LaserManager(cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT)
    particles = ParticleSystem()
    player_renderer = PlayerRenderer(cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT)
    hud = HUD(cfg.INTERNAL_WIDTH, cfg.INTERNAL_HEIGHT)
    leaderboard = Leaderboard()

    # ── Audio (best-effort: don't crash if sounds missing) ──
    sounds = _load_sounds()

    # ── Debug toggles ──
    show_fps = cfg.DEBUG_FPS
    show_debug_mask = cfg.DEBUG_MASK

    # ── Tracking variables ──
    body_lost_frames = 0      # Consecutive frames without body during gameplay
    last_frame_time = time.time()

    # ── Start the camera thread ──
    camera.start()
    print("[Dodge the Lasers] Camera thread started. Game running.")
    print("[Dodge the Lasers] Press Escape to exit, P to pause, F for FPS.")

    # ══════════════════════════════════════════════════════════════
    # MAIN GAME LOOP
    # ══════════════════════════════════════════════════════════════

    running = True
    while running:
        now = time.time()
        dt = now - last_frame_time
        last_frame_time = now
        # Clamp dt to prevent physics explosions after a pause/lag spike
        dt = min(dt, 0.1)

        # ────────────────────────────────────────────────────────
        # STEP 0: Process input events
        # ────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_p:
                    game_state.toggle_pause()
                    _play_sound(sounds, "beep")

                elif event.key == pygame.K_f:
                    show_fps = not show_fps

                elif event.key == pygame.K_d:
                    show_debug_mask = not show_debug_mask

                elif event.key == pygame.K_r and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    leaderboard.reset()
                    print("[Dodge the Lasers] Leaderboard reset.")

                # Force difficulty tiers (operator keys)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    tier = event.key - pygame.K_0
                    game_state.forced_difficulty = tier
                    print(f"[Debug] Forced difficulty tier: {tier}")

                elif event.key == pygame.K_0:
                    game_state.forced_difficulty = None
                    print("[Debug] Difficulty set to auto.")

        # Don't update anything while paused
        if game_state.state == State.PAUSED:
            game_surface.fill(cfg.COLOR_BACKGROUND)
            hud.render(game_surface, game_state, leaderboard.get_scores())
            _scale_and_flip(game_surface, display)
            clock.tick(cfg.TARGET_FPS)
            continue

        # ────────────────────────────────────────────────────────
        # STEP 1: Read body mask from camera (non-blocking)
        # ────────────────────────────────────────────────────────
        body_mask, body_detected = camera.get_body_mask()
        collision_mask = camera.get_collision_mask()

        # ────────────────────────────────────────────────────────
        # STEP 2: Update game state machine
        # ────────────────────────────────────────────────────────
        prev_state = game_state.state
        game_state.update(body_detected)

        # ── State transition side-effects ──

        # Entering COUNTDOWN → reset lasers and particles
        if game_state.state == State.COUNTDOWN and prev_state == State.IDLE:
            laser_mgr.reset()
            particles.clear()
            _play_sound(sounds, "beep")

        # Entering PLAYING from COUNTDOWN → game starts
        if game_state.state == State.PLAYING and prev_state == State.COUNTDOWN:
            _play_sound(sounds, "start")

        # Entering GAME_OVER → submit score, spawn celebration particles
        if game_state.state == State.GAME_OVER and prev_state in (State.PLAYING, State.HIT):
            rank, is_highscore = leaderboard.submit(game_state.final_time)
            game_state.set_game_over_result(rank, is_highscore)
            _play_sound(sounds, "gameover")

            if is_highscore:
                _play_sound(sounds, "highscore")
                # Celebration particles from center of screen
                particles.emit(
                    cfg.INTERNAL_WIDTH // 2,
                    cfg.INTERNAL_HEIGHT // 2,
                    cfg.PARTICLES_ON_HIGHSCORE,
                    cfg.COLOR_HIGHSCORE,
                    speed_min=3.0, speed_max=12.0,
                )

        # ────────────────────────────────────────────────────────
        # STEP 3 & 4: Spawn and update lasers
        # ────────────────────────────────────────────────────────
        if game_state.state in (State.PLAYING, State.HIT):
            laser_mgr.update(dt, game_state.survival_time)

        # ────────────────────────────────────────────────────────
        # STEP 5: Collision detection
        # ────────────────────────────────────────────────────────
        if game_state.state in (State.PLAYING, State.HIT) and not game_state.is_invincible:
            collided, hit_point, hit_color = laser_mgr.check_collision(collision_mask)

            if collided:
                alive = game_state.register_hit()
                _play_sound(sounds, "hit")

                # Spawn collision particles at the impact point
                if hit_point is not None:
                    particles.emit(
                        hit_point[0], hit_point[1],
                        cfg.PARTICLES_ON_HIT,
                        hit_color or cfg.COLOR_HIT_FLASH,
                    )

        # ────────────────────────────────────────────────────────
        # STEP 6: Update particle systems
        # ────────────────────────────────────────────────────────
        particles.update(dt)

        # ────────────────────────────────────────────────────────
        # STEP 7: Render frame
        # ────────────────────────────────────────────────────────

        # 7a. Clear to background color
        game_surface.fill(cfg.COLOR_BACKGROUND)

        # 7b. Draw laser beams (behind the body)
        if game_state.state in (State.PLAYING, State.HIT, State.GAME_OVER):
            laser_mgr.render(game_surface)

        # 7c. Draw the player's neon body silhouette
        if body_detected and game_state.state in (State.COUNTDOWN, State.PLAYING, State.HIT):
            body_surface = player_renderer.render_body(
                body_mask,
                is_invincible=game_state.is_invincible,
                time_now=now,
            )
            game_surface.blit(body_surface, (0, 0))

        # Also show body on idle screen (so approaching visitors see themselves)
        if body_detected and game_state.state == State.IDLE:
            # Dimmer version on idle
            body_surface = player_renderer.render_body(body_mask, time_now=now)
            body_surface.set_alpha(80)
            game_surface.blit(body_surface, (0, 0))

        # 7d. Draw particles (on top of everything except HUD)
        particles.render(game_surface)

        # 7e. Draw HUD (topmost layer)
        hud.render(game_surface, game_state, leaderboard.get_scores())

        # 7f. Body-lost hint during gameplay
        if game_state.state in (State.PLAYING, State.HIT) and not body_detected:
            body_lost_frames += 1
            if body_lost_frames > cfg.BODY_LOST_HINT_FRAMES:
                hud.render_body_lost_hint(game_surface)
        else:
            body_lost_frames = 0

        # 7g. Debug overlays
        if show_fps:
            hud.render_debug(game_surface, clock.get_fps(), particles.alive_count)

        if show_debug_mask:
            _render_debug_mask(game_surface, body_mask, collision_mask)

        # ────────────────────────────────────────────────────────
        # STEP 8: Scale to display resolution and flip
        # ────────────────────────────────────────────────────────
        _scale_and_flip(game_surface, display)
        clock.tick(cfg.TARGET_FPS)

    # ══════════════════════════════════════════════════════════════
    # CLEANUP
    # ══════════════════════════════════════════════════════════════
    print("[Dodge the Lasers] Shutting down...")
    camera.stop()
    pygame.quit()
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════

def _scale_and_flip(game_surface, display):
    """
    Scale the internal-resolution game surface up to the display
    resolution and present it.  Uses pygame.transform.scale which
    is hardware-accelerated on most systems.
    """
    scaled = pygame.transform.scale(
        game_surface,
        (cfg.DISPLAY_WIDTH, cfg.DISPLAY_HEIGHT),
    )
    display.blit(scaled, (0, 0))
    pygame.display.flip()


def _render_debug_mask(surface, body_mask, collision_mask):
    """
    Overlay the raw body mask (green) and collision mask (red)
    as a semi-transparent debug view in the corner.
    """
    # Scale masks down to a small preview
    scale = 0.25
    pw = int(cfg.INTERNAL_WIDTH * scale)
    ph = int(cfg.INTERNAL_HEIGHT * scale)

    debug_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)

    # Body mask in green
    for y in range(ph):
        for x in range(pw):
            oy, ox = int(y / scale), int(x / scale)
            if oy < body_mask.shape[0] and ox < body_mask.shape[1]:
                if body_mask[oy, ox] > 0:
                    debug_surf.set_at((x, y), (0, 255, 0, 100))
                if collision_mask[oy, ox] > 0:
                    debug_surf.set_at((x, y), (255, 0, 0, 150))

    surface.blit(debug_surf, (5, surface.get_height() - ph - 5))


def _load_sounds():
    """
    Attempt to load sound effects.  Returns a dict of sound objects.
    If sounds can't be loaded (missing files, audio init failure),
    returns empty dict — the game runs silently but doesn't crash.
    """
    sounds = {}
    if not cfg.ENABLE_AUDIO:
        return sounds

    # We generate simple beep sounds programmatically so there are
    # no external WAV files required for the MVP.
    try:
        import array

        sample_rate = 22050

        # Beep sound (countdown, UI feedback)
        beep_freq = 880
        beep_duration = 0.15
        beep_samples = int(sample_rate * beep_duration)
        beep_buf = array.array("h", [0] * beep_samples)
        for i in range(beep_samples):
            t = i / sample_rate
            # Sine wave with quick fade-out envelope
            envelope = max(0, 1.0 - t / beep_duration)
            val = int(16000 * envelope * np.sin(2 * np.pi * beep_freq * t))
            beep_buf[i] = max(-32768, min(32767, val))
        beep_sound = pygame.mixer.Sound(buffer=beep_buf)
        beep_sound.set_volume(cfg.AUDIO_VOLUME * 0.5)
        sounds["beep"] = beep_sound

        # Hit sound (zap/buzz)
        hit_duration = 0.25
        hit_samples = int(sample_rate * hit_duration)
        hit_buf = array.array("h", [0] * hit_samples)
        for i in range(hit_samples):
            t = i / sample_rate
            envelope = max(0, 1.0 - t / hit_duration)
            # Distorted buzz: mix of frequencies for a "zap" feel
            val = int(12000 * envelope * (
                np.sin(2 * np.pi * 150 * t) +
                0.5 * np.sin(2 * np.pi * 300 * t) +
                0.3 * np.random.uniform(-1, 1)
            ))
            hit_buf[i] = max(-32768, min(32767, val))
        hit_sound = pygame.mixer.Sound(buffer=hit_buf)
        hit_sound.set_volume(cfg.AUDIO_VOLUME * 0.7)
        sounds["hit"] = hit_sound

        # Game start sound (ascending tone)
        start_duration = 0.4
        start_samples = int(sample_rate * start_duration)
        start_buf = array.array("h", [0] * start_samples)
        for i in range(start_samples):
            t = i / sample_rate
            freq = 400 + (t / start_duration) * 800  # Sweep 400→1200 Hz
            envelope = min(1.0, t / 0.05) * max(0, 1.0 - t / start_duration)
            val = int(14000 * envelope * np.sin(2 * np.pi * freq * t))
            start_buf[i] = max(-32768, min(32767, val))
        start_sound = pygame.mixer.Sound(buffer=start_buf)
        start_sound.set_volume(cfg.AUDIO_VOLUME * 0.6)
        sounds["start"] = start_sound

        # Game over sound (descending tone)
        go_duration = 0.6
        go_samples = int(sample_rate * go_duration)
        go_buf = array.array("h", [0] * go_samples)
        for i in range(go_samples):
            t = i / sample_rate
            freq = 800 - (t / go_duration) * 600  # Sweep 800→200 Hz
            envelope = max(0, 1.0 - t / go_duration)
            val = int(14000 * envelope * np.sin(2 * np.pi * freq * t))
            go_buf[i] = max(-32768, min(32767, val))
        go_sound = pygame.mixer.Sound(buffer=go_buf)
        go_sound.set_volume(cfg.AUDIO_VOLUME * 0.6)
        sounds["gameover"] = go_sound

        # High score celebration (major chord)
        hs_duration = 1.0
        hs_samples = int(sample_rate * hs_duration)
        hs_buf = array.array("h", [0] * hs_samples)
        for i in range(hs_samples):
            t = i / sample_rate
            envelope = min(1.0, t / 0.05) * max(0, 1.0 - (t / hs_duration) ** 0.5)
            # Major chord: root + major third + fifth
            val = int(10000 * envelope * (
                np.sin(2 * np.pi * 523.25 * t) +  # C5
                np.sin(2 * np.pi * 659.25 * t) +  # E5
                np.sin(2 * np.pi * 783.99 * t)     # G5
            ))
            hs_buf[i] = max(-32768, min(32767, val))
        hs_sound = pygame.mixer.Sound(buffer=hs_buf)
        hs_sound.set_volume(cfg.AUDIO_VOLUME * 0.8)
        sounds["highscore"] = hs_sound

        print(f"[Audio] Loaded {len(sounds)} procedural sounds.")

    except Exception as e:
        print(f"[Audio] Could not initialize sounds: {e}")
        sounds = {}

    return sounds


def _play_sound(sounds, name):
    """Play a sound by name if it exists. Never crashes."""
    try:
        if name in sounds:
            sounds[name].play()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Dodge the Lasers] Interrupted by user.")
        pygame.quit()
        sys.exit(0)
    except Exception as e:
        print(f"\n[Dodge the Lasers] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        # Save crash log for post-mortem debugging
        try:
            with open("crash.log", "a") as f:
                import datetime
                f.write(f"\n{'='*60}\n")
                f.write(f"Crash at {datetime.datetime.now()}\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        pygame.quit()
        sys.exit(1)
