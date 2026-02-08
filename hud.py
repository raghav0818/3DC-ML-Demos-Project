"""
hud.py — Heads-Up Display rendering for all game states.

Renders: survival timer, lives, difficulty tier label, mini-leaderboard,
countdown numbers, game-over screen, idle/attract screen, and the
"body lost" hint.

All text rendering uses PyGame's built-in font system.  We load fonts
once at init and reuse them every frame.
"""

import math
import time
import pygame

import config as cfg
from game_state import State


class HUD:
    """
    Renders all overlay UI elements on top of the game surface.
    Each method draws onto the passed-in surface (at internal resolution).
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Initialize PyGame font system (must be called after pygame.init())
        pygame.font.init()

        # Load fonts at various sizes.  We use the default system font
        # with monospace for the timer (so digits don't shift width).
        self.font_huge = pygame.font.SysFont("arial", 72, bold=True)
        self.font_large = pygame.font.SysFont("arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.font_timer = pygame.font.SysFont("couriernew", 36, bold=True)
        self.font_countdown = pygame.font.SysFont("arial", 120, bold=True)

    # ────────────────────────────────────────────────────────────
    # Public API: render the appropriate HUD for the current state
    # ────────────────────────────────────────────────────────────

    def render(self, surface, game_state, leaderboard_scores):
        """
        Master render method.  Dispatches to the appropriate sub-renderer
        based on the current game state.
        """
        state = game_state.state

        if state == State.IDLE:
            self._render_idle(surface, leaderboard_scores)
        elif state == State.COUNTDOWN:
            self._render_countdown(surface, game_state)
        elif state in (State.PLAYING, State.HIT):
            self._render_playing(surface, game_state, leaderboard_scores)
        elif state == State.GAME_OVER:
            self._render_game_over(surface, game_state, leaderboard_scores)
        elif state == State.PAUSED:
            self._render_paused(surface)

    # ────────────────────────────────────────────────────────────
    # IDLE / Attract Screen
    # ────────────────────────────────────────────────────────────

    def _render_idle(self, surface, leaderboard_scores):
        """
        Attract screen shown when no player is present.
        Pulsing "STEP INTO THE FRAME" text + leaderboard.
        """
        # Pulsing alpha effect on the main text
        pulse = (math.sin(time.time() * cfg.IDLE_PULSE_SPEED) + 1) / 2  # 0→1
        alpha = int(120 + pulse * 135)  # Range: 120–255

        # Title
        self._draw_text_centered(
            surface, cfg.GAME_TITLE,
            self.font_large, cfg.COLOR_IDLE_TEXT,
            y=self.height // 2 - 80, alpha=alpha
        )

        # Main instruction
        self._draw_text_centered(
            surface, cfg.IDLE_TEXT_MAIN,
            self.font_medium, cfg.COLOR_HUD_TEXT,
            y=self.height // 2 - 20, alpha=alpha
        )

        # Sub text
        self._draw_text_centered(
            surface, cfg.IDLE_TEXT_SUB,
            self.font_small, (150, 150, 150),
            y=self.height // 2 + 20
        )

        # Leaderboard
        self._render_leaderboard_full(surface, leaderboard_scores)

        # Branding
        self._draw_text(
            surface, "SUTD 3DC  |  Open House 2026",
            self.font_small, (80, 80, 80),
            x=self.width // 2, y=self.height - 25,
            center_x=True
        )

    # ────────────────────────────────────────────────────────────
    # COUNTDOWN
    # ────────────────────────────────────────────────────────────

    def _render_countdown(self, surface, game_state):
        """Large 3, 2, 1 in the center of the screen."""
        num = game_state.countdown_number
        if num > 0:
            text = str(num)
            # Scale effect: number gets slightly smaller as it ages
            elapsed_in_num = game_state.time_in_state % 1.0
            scale = 1.0 + (1.0 - elapsed_in_num) * 0.3  # 1.3→1.0

            # Render at base size then we'll just use the countdown font
            self._draw_text_centered(
                surface, text,
                self.font_countdown, cfg.COLOR_COUNTDOWN,
                y=self.height // 2 - 60,
                alpha=int(255 * min(1.0, (1.0 - elapsed_in_num) * 2))
            )

        # "GET READY" subtitle
        self._draw_text_centered(
            surface, "GET READY",
            self.font_medium, cfg.COLOR_HUD_TEXT,
            y=self.height // 2 + 60
        )

    # ────────────────────────────────────────────────────────────
    # PLAYING / HIT
    # ────────────────────────────────────────────────────────────

    def _render_playing(self, surface, game_state, leaderboard_scores):
        """Timer, lives, difficulty tier, and mini leaderboard."""

        # ── Survival timer (top center) ──
        t = game_state.survival_time
        timer_text = f"{t:.1f}s"
        # Shadow
        self._draw_text(
            surface, timer_text, self.font_timer, cfg.COLOR_HUD_SHADOW,
            x=self.width // 2 + 2, y=22, center_x=True
        )
        # Main
        self._draw_text(
            surface, timer_text, self.font_timer, cfg.COLOR_HUD_TEXT,
            x=self.width // 2, y=20, center_x=True
        )

        # ── Lives (top left) ──
        self._render_lives(surface, game_state.lives)

        # ── Difficulty tier (top right) ──
        tier_name, tier_color = game_state.difficulty_tier
        self._draw_text(
            surface, tier_name, self.font_small, tier_color,
            x=self.width - 15, y=15, align_right=True
        )

        # ── Mini leaderboard (bottom right, top 3 only) ──
        self._render_leaderboard_mini(surface, leaderboard_scores)

        # ── Gameplay instruction (first few seconds) ──
        T = game_state.survival_time
        if T < 8.0:
            inst_alpha = 255 if T < 5.0 else int(255 * (1.0 - (T - 5.0) / 3.0))
            self._draw_text_centered(
                surface, "MOVE TO THE GREEN ZONES",
                self.font_medium, (0, 255, 100),
                y=self.height - 55, alpha=inst_alpha
            )

        # ── Hit flash overlay ──
        if game_state.state == State.HIT:
            flash_progress = game_state.time_in_state / cfg.HIT_FLASH_DURATION
            if flash_progress < 1.0:
                alpha = int(cfg.HIT_FLASH_ALPHA * (1.0 - flash_progress))
                flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                flash_surf.fill((*cfg.COLOR_HIT_FLASH, alpha))
                surface.blit(flash_surf, (0, 0))

    def _render_lives(self, surface, lives):
        """Draw heart/circle icons for remaining lives."""
        for i in range(cfg.STARTING_LIVES):
            cx = 20 + i * 28
            cy = 20
            if i < lives:
                # Filled circle (alive)
                pygame.draw.circle(surface, (255, 60, 60), (cx, cy), 10)
                pygame.draw.circle(surface, (255, 120, 120), (cx, cy), 6)
            else:
                # Empty circle (lost)
                pygame.draw.circle(surface, (80, 80, 80), (cx, cy), 10, 2)

    # ────────────────────────────────────────────────────────────
    # GAME OVER
    # ────────────────────────────────────────────────────────────

    def _render_game_over(self, surface, game_state, leaderboard_scores):
        """
        Game over screen: final time, rank, high-score celebration,
        and full leaderboard.
        """
        # Darken background
        dark = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 150))
        surface.blit(dark, (0, 0))

        # GAME OVER title
        self._draw_text_centered(
            surface, "GAME OVER",
            self.font_large, cfg.COLOR_GAMEOVER,
            y=self.height // 2 - 100
        )

        # Final time
        time_text = f"{game_state.final_time:.1f} seconds"
        self._draw_text_centered(
            surface, time_text,
            self.font_timer, cfg.COLOR_IDLE_TEXT,
            y=self.height // 2 - 40
        )

        # Rank
        if game_state.leaderboard_rank >= 0:
            rank_text = f"RANK #{game_state.leaderboard_rank + 1}"
            color = cfg.COLOR_HIGHSCORE if game_state.is_new_highscore else cfg.COLOR_HUD_TEXT
            self._draw_text_centered(
                surface, rank_text,
                self.font_medium, color,
                y=self.height // 2 + 10
            )

        # New high score celebration text
        if game_state.is_new_highscore:
            pulse = (math.sin(time.time() * 6) + 1) / 2
            alpha = int(180 + pulse * 75)
            self._draw_text_centered(
                surface, "NEW HIGH SCORE!",
                self.font_medium, cfg.COLOR_HIGHSCORE,
                y=self.height // 2 + 50, alpha=alpha
            )

        # Mini leaderboard
        self._render_leaderboard_full(surface, leaderboard_scores, y_start=self.height // 2 + 90)

    # ────────────────────────────────────────────────────────────
    # PAUSED
    # ────────────────────────────────────────────────────────────

    def _render_paused(self, surface):
        """Simple pause overlay."""
        dark = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 180))
        surface.blit(dark, (0, 0))

        self._draw_text_centered(
            surface, "PAUSED",
            self.font_large, cfg.COLOR_HUD_TEXT,
            y=self.height // 2 - 30
        )
        self._draw_text_centered(
            surface, "Press P to resume",
            self.font_small, (150, 150, 150),
            y=self.height // 2 + 30
        )

    # ────────────────────────────────────────────────────────────
    # Leaderboard rendering
    # ────────────────────────────────────────────────────────────

    def _render_leaderboard_mini(self, surface, scores):
        """Small leaderboard in bottom-right during gameplay (top 3)."""
        if not scores:
            return
        top = scores[:3]
        y = self.height - 15 - len(top) * 18
        self._draw_text(surface, "TOP SCORES", self.font_small, (100, 100, 100),
                        x=self.width - 15, y=y - 18, align_right=True)
        for i, score in enumerate(top):
            text = f"#{i+1}  {score:.1f}s"
            color = cfg.COLOR_HIGHSCORE if i == 0 else (150, 150, 150)
            self._draw_text(surface, text, self.font_small, color,
                            x=self.width - 15, y=y + i * 18, align_right=True)

    def _render_leaderboard_full(self, surface, scores, y_start=None):
        """Full leaderboard displayed on idle and game-over screens."""
        if not scores:
            return

        y = y_start or (self.height - 30 - min(len(scores), 10) * 20)
        top = scores[:10]

        for i, score in enumerate(top):
            text = f"#{i+1:>2}   {score:.1f}s"
            if i == 0:
                color = cfg.COLOR_HIGHSCORE
            elif i < 3:
                color = cfg.COLOR_IDLE_TEXT
            else:
                color = (120, 120, 120)
            self._draw_text(surface, text, self.font_small, color,
                            x=self.width // 2, y=y + i * 20, center_x=True)

    # ────────────────────────────────────────────────────────────
    # Body-lost hint
    # ────────────────────────────────────────────────────────────

    # ────────────────────────────────────────────────────────────
    # Anti-camping reticle
    # ────────────────────────────────────────────────────────────

    def render_camp_warning(self, surface, target_x, target_y):
        """Draw a targeting reticle + 'MOVE!' on the camper's position."""
        now = time.time()
        pulse = abs(math.sin(now * 6))
        alpha = int(150 + pulse * 105)
        color = (255, 0, 0, alpha)

        reticle_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        size = 30
        thickness = 2
        # Crosshair lines
        pygame.draw.line(reticle_surf, color,
                         (target_x - size, target_y),
                         (target_x + size, target_y), thickness)
        pygame.draw.line(reticle_surf, color,
                         (target_x, target_y - size),
                         (target_x, target_y + size), thickness)
        # Outer circle
        pygame.draw.circle(reticle_surf, color, (target_x, target_y),
                           size, thickness)
        # Inner circle
        pygame.draw.circle(reticle_surf, color, (target_x, target_y),
                           size // 2, thickness)

        surface.blit(reticle_surf, (0, 0))

        # "MOVE!" text above the reticle
        self._draw_text_centered(
            surface, "MOVE!",
            self.font_medium, (255, 0, 0),
            y=max(0, target_y - 55), alpha=alpha
        )

    # ────────────────────────────────────────────────────────────
    # Body-lost hint
    # ────────────────────────────────────────────────────────────

    def render_body_lost_hint(self, surface):
        """Shown when body tracking is lost during gameplay."""
        self._draw_text_centered(
            surface, "STEP CLOSER",
            self.font_medium, cfg.COLOR_LASER_SWEEP,
            y=self.height // 2 + 80
        )

    # ────────────────────────────────────────────────────────────
    # Debug overlay
    # ────────────────────────────────────────────────────────────

    def render_debug(self, surface, fps, particle_count):
        """FPS counter and particle count (toggled with F key)."""
        texts = [
            f"FPS: {fps:.0f}",
            f"Particles: {particle_count}",
        ]
        for i, t in enumerate(texts):
            self._draw_text(surface, t, self.font_small, (0, 255, 0),
                            x=10, y=self.height - 50 + i * 20)

    # ────────────────────────────────────────────────────────────
    # Text drawing helpers
    # ────────────────────────────────────────────────────────────

    def _draw_text(self, surface, text, font, color, x, y,
                   center_x=False, align_right=False, alpha=255):
        """Draw text at a specific position with optional alignment."""
        rendered = font.render(text, True, color)
        if alpha < 255:
            rendered.set_alpha(alpha)
        rect = rendered.get_rect()
        if center_x:
            rect.centerx = x
        elif align_right:
            rect.right = x
        else:
            rect.left = x
        rect.top = y
        surface.blit(rendered, rect)

    def _draw_text_centered(self, surface, text, font, color, y, alpha=255):
        """Draw text horizontally centered at a given y coordinate."""
        self._draw_text(surface, text, font, color,
                        x=self.width // 2, y=y, center_x=True, alpha=alpha)
