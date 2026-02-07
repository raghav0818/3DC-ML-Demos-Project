"""
laser.py — Laser beam system.

Beams appear at fixed positions with a gap the player must dodge into.
Each beam goes through two phases:
  1. WARNING: previews where the beam will appear + highlights the safe gap
  2. ACTIVE: beam is fully visible and causes collision damage

Beam types:
  - Horizontal (cyan): full-width line at a fixed Y, gap along X axis
  - Vertical (magenta): full-height line at a fixed X, gap along Y axis
  - Cross: simultaneous horizontal + vertical beams

Difficulty parameters are computed from the survival time T using
the formulas in config.py.
"""

import random
import math
import numpy as np
import pygame

import config as cfg


# ────────────────────────────────────────────────────────────
# Difficulty helpers
# ────────────────────────────────────────────────────────────

def get_spawn_interval(T):
    """Seconds between beam spawns."""
    interval = cfg.SPAWN_BASE_INTERVAL - T * cfg.SPAWN_INTERVAL_DECAY
    return max(cfg.SPAWN_MIN_INTERVAL, interval)


def get_gap_fraction(T):
    """Gap size as fraction of screen dimension."""
    gap = cfg.GAP_BASE_SIZE - T * cfg.GAP_SHRINK_RATE
    return max(cfg.GAP_MIN_SIZE, gap)


def get_warning_ms(T):
    """Warning duration in milliseconds."""
    warning = cfg.WARNING_BASE_MS - T * cfg.WARNING_DECAY
    return max(cfg.WARNING_MIN_MS, warning)


def get_active_duration(T):
    """How long the beam stays active (visible and dangerous)."""
    duration = cfg.BEAM_ACTIVE_BASE - T * cfg.BEAM_ACTIVE_DECAY
    return max(cfg.BEAM_ACTIVE_MIN, duration)


def get_available_types(T):
    """Return list of beam types unlocked at time T."""
    types = ["horizontal"]
    if T >= cfg.UNLOCK_VERTICAL:
        types.append("vertical")
    if T >= cfg.UNLOCK_CROSS:
        types.append("cross")
    return types


# Safe zone indicator color
COLOR_SAFE_ZONE = (0, 255, 100)


# ────────────────────────────────────────────────────────────
# Laser beam class
# ────────────────────────────────────────────────────────────

class Laser:
    """
    A laser beam at a fixed position with a dodgeable gap.

    Lifecycle:
      1. WARNING phase — faint beam preview + highlighted safe gap
      2. ACTIVE phase  — full beam with glow, collision enabled
      3. Removed when active timer expires
    """

    PHASE_WARNING = "warning"
    PHASE_ACTIVE = "active"

    def __init__(self, beam_type, T, screen_w, screen_h):
        self.beam_type = beam_type
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.alive = True

        # Timing
        self.warning_duration = get_warning_ms(T) / 1000.0
        self.active_duration = get_active_duration(T)
        self.phase = self.PHASE_WARNING
        self.phase_timer = self.warning_duration
        self.beam_width = cfg.BEAM_CORE_WIDTH

        # Gap
        gap_frac = get_gap_fraction(T)

        if beam_type == "horizontal":
            self._setup_horizontal(gap_frac)
        elif beam_type == "vertical":
            self._setup_vertical(gap_frac)
        elif beam_type == "cross":
            self._setup_cross(gap_frac)

    # ── Setup methods ──

    def _setup_horizontal(self, gap_frac):
        """Full-width beam at a fixed Y, gap along X axis."""
        self.color = cfg.COLOR_LASER_HORIZONTAL
        margin = 60
        self.y_pos = random.randint(margin, self.screen_h - margin)
        gap_w = int(self.screen_w * gap_frac)
        gap_margin = gap_w // 2 + 20
        self.gap_center_x = random.randint(gap_margin, self.screen_w - gap_margin)
        self.gap_size = gap_w

    def _setup_vertical(self, gap_frac):
        """Full-height beam at a fixed X, gap along Y axis."""
        self.color = cfg.COLOR_LASER_VERTICAL
        margin = 60
        self.x_pos = random.randint(margin, self.screen_w - margin)
        gap_h = int(self.screen_h * gap_frac)
        gap_margin = gap_h // 2 + 20
        self.gap_center_y = random.randint(gap_margin, self.screen_h - gap_margin)
        self.gap_size = gap_h

    def _setup_cross(self, gap_frac):
        """Simultaneous horizontal + vertical beams."""
        self.color_h = cfg.COLOR_LASER_CROSS_H
        self.color_v = cfg.COLOR_LASER_CROSS_V

        h_margin = 60
        v_margin = 60
        self.y_pos = random.randint(h_margin, self.screen_h - h_margin)
        self.x_pos = random.randint(v_margin, self.screen_w - v_margin)

        gap_w = int(self.screen_w * gap_frac)
        gap_h = int(self.screen_h * gap_frac)
        gap_margin_w = gap_w // 2 + 20
        gap_margin_h = gap_h // 2 + 20

        self.h_gap_center_x = random.randint(gap_margin_w, self.screen_w - gap_margin_w)
        self.h_gap_size = gap_w
        self.v_gap_center_y = random.randint(gap_margin_h, self.screen_h - gap_margin_h)
        self.v_gap_size = gap_h

    # ────────────────────────────────────────────────────────────
    # Update
    # ────────────────────────────────────────────────────────────

    def update(self, dt):
        """Advance the beam lifecycle. Returns False when beam should be removed."""
        self.phase_timer -= dt

        if self.phase == self.PHASE_WARNING:
            if self.phase_timer <= 0:
                self.phase = self.PHASE_ACTIVE
                self.phase_timer = self.active_duration
            return True

        elif self.phase == self.PHASE_ACTIVE:
            if self.phase_timer <= 0:
                self.alive = False
            return self.alive

        return self.alive

    # ────────────────────────────────────────────────────────────
    # Collision mask
    # ────────────────────────────────────────────────────────────

    def get_collision_mask(self):
        """Return collision mask (only during ACTIVE phase)."""
        if self.phase != self.PHASE_ACTIVE:
            return None

        mask = np.zeros((self.screen_h, self.screen_w), dtype=np.uint8)

        if self.beam_type == "horizontal":
            self._fill_h_mask(mask, self.y_pos, self.gap_center_x, self.gap_size)
        elif self.beam_type == "vertical":
            self._fill_v_mask(mask, self.x_pos, self.gap_center_y, self.gap_size)
        elif self.beam_type == "cross":
            self._fill_h_mask(mask, self.y_pos, self.h_gap_center_x, self.h_gap_size)
            self._fill_v_mask(mask, self.x_pos, self.v_gap_center_y, self.v_gap_size)

        return mask

    def _fill_h_mask(self, mask, y, gap_cx, gap_size):
        """Fill horizontal beam collision area (full width with gap)."""
        bw = self.beam_width // 2
        y_top = max(0, y - bw)
        y_bot = min(self.screen_h, y + bw)
        if y_top >= y_bot:
            return
        mask[y_top:y_bot, :] = 255
        gap_l = max(0, gap_cx - gap_size // 2)
        gap_r = min(self.screen_w, gap_cx + gap_size // 2)
        mask[y_top:y_bot, gap_l:gap_r] = 0

    def _fill_v_mask(self, mask, x, gap_cy, gap_size):
        """Fill vertical beam collision area (full height with gap)."""
        bw = self.beam_width // 2
        x_l = max(0, x - bw)
        x_r = min(self.screen_w, x + bw)
        if x_l >= x_r:
            return
        mask[:, x_l:x_r] = 255
        gap_t = max(0, gap_cy - gap_size // 2)
        gap_b = min(self.screen_h, gap_cy + gap_size // 2)
        mask[gap_t:gap_b, x_l:x_r] = 0

    # ────────────────────────────────────────────────────────────
    # Rendering
    # ────────────────────────────────────────────────────────────

    def render(self, surface):
        """Draw the beam onto the game surface."""
        if self.phase == self.PHASE_WARNING:
            self._render_warning(surface)
        elif self.phase == self.PHASE_ACTIVE:
            self._render_active(surface)

    def _get_primary_color(self):
        """Get the main color (for particles on collision)."""
        if self.beam_type == "cross":
            return self.color_h
        return self.color

    # ── Warning rendering ──

    def _render_warning(self, surface):
        """Show beam preview with highlighted safe gap."""
        progress = 1.0 - (self.phase_timer / self.warning_duration)  # 0→1
        pulse = abs(math.sin(progress * math.pi * 6)) * 0.5 + 0.3

        if self.beam_type == "horizontal":
            self._render_warning_h(surface, pulse, self.y_pos,
                                   self.gap_center_x, self.gap_size, self.color)
        elif self.beam_type == "vertical":
            self._render_warning_v(surface, pulse, self.x_pos,
                                   self.gap_center_y, self.gap_size, self.color)
        elif self.beam_type == "cross":
            self._render_warning_h(surface, pulse, self.y_pos,
                                   self.h_gap_center_x, self.h_gap_size, self.color_h)
            self._render_warning_v(surface, pulse, self.x_pos,
                                   self.v_gap_center_y, self.v_gap_size, self.color_v)

    def _render_warning_h(self, surface, pulse, y, gap_cx, gap_size, color):
        """Warning indicator for horizontal beam: faint line + green gap."""
        w = surface.get_width()
        bw = self.beam_width // 2
        gap_l = gap_cx - gap_size // 2
        gap_r = gap_cx + gap_size // 2

        warn_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Faint beam preview (danger zones)
        beam_alpha = int(pulse * 60)
        beam_color = (*color, beam_alpha)
        if gap_l > 0:
            pygame.draw.rect(warn_surf, beam_color, (0, y - bw, gap_l, bw * 2))
        if gap_r < w:
            pygame.draw.rect(warn_surf, beam_color,
                             (gap_r, y - bw, w - gap_r, bw * 2))

        # Safe zone: faint green fill
        gap_h = bw * 2 + 30
        safe_fill_alpha = int(pulse * 40)
        pygame.draw.rect(warn_surf, (*COLOR_SAFE_ZONE, safe_fill_alpha),
                         (gap_l, y - gap_h // 2, gap_size, gap_h))

        # Safe zone: green brackets [ ]
        bracket_alpha = int(pulse * 200)
        bracket_color = (*COLOR_SAFE_ZONE, bracket_alpha)
        bk_w = 4
        bk_arm = 14
        # Left bracket [
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_l, y - gap_h // 2, bk_w, gap_h))
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_l, y - gap_h // 2, bk_arm, bk_w))
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_l, y + gap_h // 2 - bk_w, bk_arm, bk_w))
        # Right bracket ]
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_r - bk_w, y - gap_h // 2, bk_w, gap_h))
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_r - bk_arm, y - gap_h // 2, bk_arm, bk_w))
        pygame.draw.rect(warn_surf, bracket_color,
                         (gap_r - bk_arm, y + gap_h // 2 - bk_w, bk_arm, bk_w))

        surface.blit(warn_surf, (0, 0))

    def _render_warning_v(self, surface, pulse, x, gap_cy, gap_size, color):
        """Warning indicator for vertical beam: faint line + green gap."""
        h = surface.get_height()
        bw = self.beam_width // 2
        gap_t = gap_cy - gap_size // 2
        gap_b = gap_cy + gap_size // 2

        warn_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Faint beam preview (danger zones)
        beam_alpha = int(pulse * 60)
        beam_color = (*color, beam_alpha)
        if gap_t > 0:
            pygame.draw.rect(warn_surf, beam_color, (x - bw, 0, bw * 2, gap_t))
        if gap_b < h:
            pygame.draw.rect(warn_surf, beam_color,
                             (x - bw, gap_b, bw * 2, h - gap_b))

        # Safe zone: faint green fill
        gap_w = bw * 2 + 30
        safe_fill_alpha = int(pulse * 40)
        pygame.draw.rect(warn_surf, (*COLOR_SAFE_ZONE, safe_fill_alpha),
                         (x - gap_w // 2, gap_t, gap_w, gap_size))

        # Safe zone: green brackets (top and bottom)
        bracket_alpha = int(pulse * 200)
        bracket_color = (*COLOR_SAFE_ZONE, bracket_alpha)
        bk_h = 4
        bk_arm = 14
        # Top bracket
        pygame.draw.rect(warn_surf, bracket_color,
                         (x - gap_w // 2, gap_t, gap_w, bk_h))
        pygame.draw.rect(warn_surf, bracket_color,
                         (x - gap_w // 2, gap_t, bk_h, bk_arm))
        pygame.draw.rect(warn_surf, bracket_color,
                         (x + gap_w // 2 - bk_h, gap_t, bk_h, bk_arm))
        # Bottom bracket
        pygame.draw.rect(warn_surf, bracket_color,
                         (x - gap_w // 2, gap_b - bk_h, gap_w, bk_h))
        pygame.draw.rect(warn_surf, bracket_color,
                         (x - gap_w // 2, gap_b - bk_arm, bk_h, bk_arm))
        pygame.draw.rect(warn_surf, bracket_color,
                         (x + gap_w // 2 - bk_h, gap_b - bk_arm, bk_h, bk_arm))

        surface.blit(warn_surf, (0, 0))

    # ── Active rendering ──

    def _render_active(self, surface):
        """Render the full beam with glow at its fixed position."""
        # Flash-in effect during first 0.15 seconds
        time_active = self.active_duration - self.phase_timer
        flash_mult = min(1.0, time_active / 0.15)

        # Fade-out during last 0.3 seconds (visual hint that beam is ending)
        fade_mult = min(1.0, self.phase_timer / 0.3)

        alpha_mult = flash_mult * fade_mult

        if self.beam_type == "horizontal":
            self._render_h_beam(surface, self.y_pos, self.gap_center_x,
                                self.gap_size, self.color, alpha_mult)
        elif self.beam_type == "vertical":
            self._render_v_beam(surface, self.x_pos, self.gap_center_y,
                                self.gap_size, self.color, alpha_mult)
        elif self.beam_type == "cross":
            self._render_h_beam(surface, self.y_pos, self.h_gap_center_x,
                                self.h_gap_size, self.color_h, alpha_mult)
            self._render_v_beam(surface, self.x_pos, self.v_gap_center_y,
                                self.v_gap_size, self.color_v, alpha_mult)

    def _render_h_beam(self, surface, y, gap_cx, gap_size, color, alpha_mult=1.0):
        """Render a horizontal beam with glow layers and gap."""
        w = surface.get_width()
        bw = self.beam_width // 2
        gap_l = gap_cx - gap_size // 2
        gap_r = gap_cx + gap_size // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Outer glow
        outer_bw = bw + cfg.BEAM_OUTER_GLOW
        outer_alpha = int(cfg.BEAM_OUTER_ALPHA * 255 * alpha_mult)
        outer_color = (*color, outer_alpha)
        if gap_l > 0:
            pygame.draw.rect(glow_surf, outer_color,
                             (0, y - outer_bw, gap_l, outer_bw * 2))
        if gap_r < w:
            pygame.draw.rect(glow_surf, outer_color,
                             (gap_r, y - outer_bw, w - gap_r, outer_bw * 2))

        # Inner glow
        inner_bw = bw + cfg.BEAM_INNER_GLOW
        inner_alpha = int(cfg.BEAM_INNER_ALPHA * 255 * alpha_mult)
        inner_color = (*color, inner_alpha)
        if gap_l > 0:
            pygame.draw.rect(glow_surf, inner_color,
                             (0, y - inner_bw, gap_l, inner_bw * 2))
        if gap_r < w:
            pygame.draw.rect(glow_surf, inner_color,
                             (gap_r, y - inner_bw, w - gap_r, inner_bw * 2))

        # Core beam
        core_alpha = int(220 * alpha_mult)
        core_color = (*color, core_alpha)
        if gap_l > 0:
            pygame.draw.rect(glow_surf, core_color,
                             (0, y - bw, gap_l, bw * 2))
        if gap_r < w:
            pygame.draw.rect(glow_surf, core_color,
                             (gap_r, y - bw, w - gap_r, bw * 2))

        surface.blit(glow_surf, (0, 0))

    def _render_v_beam(self, surface, x, gap_cy, gap_size, color, alpha_mult=1.0):
        """Render a vertical beam with glow layers and gap."""
        h = surface.get_height()
        bw = self.beam_width // 2
        gap_t = gap_cy - gap_size // 2
        gap_b = gap_cy + gap_size // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Outer glow
        outer_bw = bw + cfg.BEAM_OUTER_GLOW
        outer_alpha = int(cfg.BEAM_OUTER_ALPHA * 255 * alpha_mult)
        outer_color = (*color, outer_alpha)
        if gap_t > 0:
            pygame.draw.rect(glow_surf, outer_color,
                             (x - outer_bw, 0, outer_bw * 2, gap_t))
        if gap_b < h:
            pygame.draw.rect(glow_surf, outer_color,
                             (x - outer_bw, gap_b, outer_bw * 2, h - gap_b))

        # Inner glow
        inner_bw = bw + cfg.BEAM_INNER_GLOW
        inner_alpha = int(cfg.BEAM_INNER_ALPHA * 255 * alpha_mult)
        inner_color = (*color, inner_alpha)
        if gap_t > 0:
            pygame.draw.rect(glow_surf, inner_color,
                             (x - inner_bw, 0, inner_bw * 2, gap_t))
        if gap_b < h:
            pygame.draw.rect(glow_surf, inner_color,
                             (x - inner_bw, gap_b, inner_bw * 2, h - gap_b))

        # Core
        core_alpha = int(220 * alpha_mult)
        core_color = (*color, core_alpha)
        if gap_t > 0:
            pygame.draw.rect(glow_surf, core_color,
                             (x - bw, 0, bw * 2, gap_t))
        if gap_b < h:
            pygame.draw.rect(glow_surf, core_color,
                             (x - bw, gap_b, bw * 2, h - gap_b))

        surface.blit(glow_surf, (0, 0))


# ────────────────────────────────────────────────────────────
# Laser Manager
# ────────────────────────────────────────────────────────────

class LaserManager:
    """
    Owns all active lasers. Handles spawn timing, updates, rendering,
    and collision checking against the body mask.
    """

    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.lasers = []
        self.time_since_spawn = 0.0

    def reset(self):
        """Clear all lasers (called on game start)."""
        self.lasers.clear()
        self.time_since_spawn = 0.0

    def update(self, dt, survival_time):
        """
        Spawn new lasers if the interval has elapsed, update all
        existing lasers, and remove dead ones.
        """
        T = survival_time

        # Spawn logic
        self.time_since_spawn += dt
        interval = get_spawn_interval(T)

        if self.time_since_spawn >= interval:
            self.time_since_spawn = 0.0
            self._spawn_laser(T)

        # Update all lasers
        self.lasers = [laser for laser in self.lasers
                       if laser.update(dt) and laser.alive]

    def _spawn_laser(self, T):
        """Spawn a random laser based on current difficulty."""
        available = get_available_types(T)
        beam_type = random.choice(available)
        laser = Laser(beam_type, T, self.screen_w, self.screen_h)
        self.lasers.append(laser)

    def check_collision(self, body_mask):
        """
        Check if any active laser collides with the body mask.
        Returns (collided: bool, collision_point: tuple or None,
        hit_color: tuple or None).
        """
        for laser in self.lasers:
            laser_mask = laser.get_collision_mask()
            if laser_mask is None:
                continue

            # The actual collision check: single vectorized operation
            overlap = body_mask & laser_mask
            if np.any(overlap):
                # Find approximate collision point (centroid of overlap)
                ys, xs = np.where(overlap > 0)
                if len(xs) > 0:
                    cx = int(np.mean(xs))
                    cy = int(np.mean(ys))
                    color = laser._get_primary_color()
                    return True, (cx, cy), color

        return False, None, None

    def render(self, surface):
        """Draw all active lasers onto the given surface."""
        for laser in self.lasers:
            laser.render(surface)
