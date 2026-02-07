"""
laser.py — Laser beam system.

Handles spawning, movement, rendering, warning indicators, and
collision mask generation for all four beam types:
  - Horizontal (cyan, left/right)
  - Vertical (magenta, top-down)
  - Cross (simultaneous H+V)
  - Sweep (thin gold beam, slow pan)

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

def get_beam_speed(T):
    """Beam speed (pixels/frame) as a function of survival time T."""
    speed = cfg.BEAM_BASE_SPEED + (T / 60.0) * cfg.BEAM_SPEED_RAMP
    return min(speed, cfg.BEAM_MAX_SPEED)


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


def get_available_types(T):
    """Return list of beam types unlocked at time T."""
    types = ["horizontal"]
    if T >= cfg.UNLOCK_VERTICAL:
        types.append("vertical")
    if T >= cfg.UNLOCK_CROSS:
        types.append("cross")
    if T >= cfg.UNLOCK_SWEEP:
        types.append("sweep")
    return types


# ────────────────────────────────────────────────────────────
# Laser beam class
# ────────────────────────────────────────────────────────────

class Laser:
    """
    A single laser beam (or beam pair for cross type).

    Lifecycle:
      1. Created in WARNING phase (indicator shown on screen edge)
      2. Transitions to ACTIVE when warning timer expires
      3. Moves across the screen at beam_speed
      4. Removed when fully off-screen
    """

    def __init__(self, beam_type, T, screen_w, screen_h):
        self.beam_type = beam_type   # "horizontal", "vertical", "cross", "sweep"
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.alive = True

        # Timing
        self.warning_duration = get_warning_ms(T) / 1000.0  # Convert to seconds
        self.warning_timer = self.warning_duration
        self.is_warning = True       # True = still in warning phase

        # Speed
        base_speed = get_beam_speed(T)

        # Gap
        gap_frac = get_gap_fraction(T)

        # Set up geometry based on type
        if beam_type == "horizontal":
            self._setup_horizontal(base_speed, gap_frac)
        elif beam_type == "vertical":
            self._setup_vertical(base_speed, gap_frac)
        elif beam_type == "cross":
            self._setup_cross(base_speed, gap_frac)
        elif beam_type == "sweep":
            self._setup_sweep(base_speed)

    # ── Setup methods for each beam type ──

    def _setup_horizontal(self, speed, gap_frac):
        """A full-width beam with a gap, moving vertically (top to bottom or bottom to top)."""
        self.color = cfg.COLOR_LASER_HORIZONTAL
        self.direction = random.choice(["down", "up"])
        self.speed = speed

        # Gap position (center of gap, in pixels)
        gap_h = int(self.screen_h * gap_frac)
        margin = gap_h // 2 + 10  # Keep gap away from extreme edges
        self.gap_center = random.randint(margin, self.screen_h - margin)
        self.gap_size = gap_h
        self.beam_width = cfg.BEAM_CORE_WIDTH

        # Position: the leading edge of the beam group
        if self.direction == "down":
            self.pos = -self.beam_width    # Start above screen
        else:
            self.pos = self.screen_h       # Start below screen

        # Warning indicator edge
        self.warn_edge = "top" if self.direction == "down" else "bottom"

    def _setup_vertical(self, speed, gap_frac):
        """A full-height beam with a gap, moving horizontally."""
        self.color = cfg.COLOR_LASER_VERTICAL
        self.direction = random.choice(["right", "left"])
        self.speed = speed

        gap_w = int(self.screen_w * gap_frac)
        margin = gap_w // 2 + 10
        self.gap_center = random.randint(margin, self.screen_w - margin)
        self.gap_size = gap_w
        self.beam_width = cfg.BEAM_CORE_WIDTH

        if self.direction == "right":
            self.pos = -self.beam_width
        else:
            self.pos = self.screen_w

        self.warn_edge = "left" if self.direction == "right" else "right"

    def _setup_cross(self, speed, gap_frac):
        """Simultaneous horizontal + vertical beams."""
        # We store two sub-beams
        self.color_h = cfg.COLOR_LASER_CROSS_H
        self.color_v = cfg.COLOR_LASER_CROSS_V
        self.speed = speed
        self.beam_width = cfg.BEAM_CORE_WIDTH

        gap_h = int(self.screen_h * gap_frac)
        gap_w = int(self.screen_w * gap_frac)

        margin_h = gap_h // 2 + 10
        margin_w = gap_w // 2 + 10

        # Horizontal sub-beam (moves down)
        self.h_gap_center = random.randint(margin_h, self.screen_h - margin_h)
        self.h_gap_size = gap_h
        self.h_pos = -self.beam_width
        self.h_direction = "down"

        # Vertical sub-beam (moves right)
        self.v_gap_center = random.randint(margin_w, self.screen_w - margin_w)
        self.v_gap_size = gap_w
        self.v_pos = -self.beam_width
        self.v_direction = "right"

        self.warn_edge = "top"  # Simplified: just warn from top

    def _setup_sweep(self, speed):
        """A thin beam that sweeps across — no gap, pure reaction test."""
        self.color = cfg.COLOR_LASER_SWEEP
        self.beam_width = cfg.SWEEP_BEAM_WIDTH
        self.speed = speed * cfg.SWEEP_SPEED_MULTIPLIER  # Slower

        # Sweep can be horizontal (player ducks/jumps) or vertical (player sidesteps)
        self.sweep_axis = random.choice(["horizontal", "vertical"])

        if self.sweep_axis == "horizontal":
            self.direction = random.choice(["down", "up"])
            if self.direction == "down":
                self.pos = -self.beam_width
            else:
                self.pos = self.screen_h
            self.warn_edge = "top" if self.direction == "down" else "bottom"
        else:
            self.direction = random.choice(["right", "left"])
            if self.direction == "right":
                self.pos = -self.beam_width
            else:
                self.pos = self.screen_w
            self.warn_edge = "left" if self.direction == "right" else "right"

    # ────────────────────────────────────────────────────────────
    # Update (called once per frame)
    # ────────────────────────────────────────────────────────────

    def update(self, dt):
        """
        Advance the beam by one frame.  dt is seconds since last frame.
        Returns False if the beam should be removed (off-screen).
        """
        # Warning phase countdown
        if self.is_warning:
            self.warning_timer -= dt
            if self.warning_timer <= 0:
                self.is_warning = False
            return True  # Still alive during warning

        # Movement phase
        if self.beam_type == "cross":
            return self._update_cross()
        elif self.beam_type == "sweep":
            return self._update_sweep()
        else:
            return self._update_standard()

    def _update_standard(self):
        """Update for horizontal/vertical beams."""
        if self.direction in ("down", "right"):
            self.pos += self.speed
        else:
            self.pos -= self.speed

        # Check if fully off-screen
        if self.beam_type == "horizontal":
            if self.direction == "down" and self.pos > self.screen_h + self.beam_width:
                self.alive = False
            elif self.direction == "up" and self.pos < -self.beam_width:
                self.alive = False
        else:  # vertical
            if self.direction == "right" and self.pos > self.screen_w + self.beam_width:
                self.alive = False
            elif self.direction == "left" and self.pos < -self.beam_width:
                self.alive = False

        return self.alive

    def _update_cross(self):
        """Update both sub-beams of a cross."""
        self.h_pos += self.speed
        self.v_pos += self.speed

        h_gone = self.h_pos > self.screen_h + self.beam_width
        v_gone = self.v_pos > self.screen_w + self.beam_width

        if h_gone and v_gone:
            self.alive = False
        return self.alive

    def _update_sweep(self):
        """Update sweep beam."""
        if self.direction in ("down", "right"):
            self.pos += self.speed
        else:
            self.pos -= self.speed

        if self.sweep_axis == "horizontal":
            if self.direction == "down" and self.pos > self.screen_h + self.beam_width:
                self.alive = False
            elif self.direction == "up" and self.pos < -self.beam_width:
                self.alive = False
        else:
            if self.direction == "right" and self.pos > self.screen_w + self.beam_width:
                self.alive = False
            elif self.direction == "left" and self.pos < -self.beam_width:
                self.alive = False

        return self.alive

    # ────────────────────────────────────────────────────────────
    # Collision mask generation
    # ────────────────────────────────────────────────────────────

    def get_collision_mask(self):
        """
        Return a binary uint8 numpy array (screen_h × screen_w) where
        255 = laser pixel, 0 = empty.  Used for np.any(body & laser).
        Returns None if beam is still in warning phase.
        """
        if self.is_warning:
            return None

        mask = np.zeros((self.screen_h, self.screen_w), dtype=np.uint8)

        if self.beam_type == "horizontal":
            self._fill_h_beam_mask(mask, self.pos, self.gap_center, self.gap_size)
        elif self.beam_type == "vertical":
            self._fill_v_beam_mask(mask, self.pos, self.gap_center, self.gap_size)
        elif self.beam_type == "cross":
            self._fill_h_beam_mask(mask, self.h_pos, self.h_gap_center, self.h_gap_size)
            self._fill_v_beam_mask(mask, self.v_pos, self.v_gap_center, self.v_gap_size)
        elif self.beam_type == "sweep":
            if self.sweep_axis == "horizontal":
                self._fill_sweep_h_mask(mask)
            else:
                self._fill_sweep_v_mask(mask)

        return mask

    def _fill_h_beam_mask(self, mask, y_pos, gap_center, gap_size):
        """Fill horizontal beam collision area (full width with gap)."""
        y = int(y_pos)
        bw = self.beam_width // 2
        y_top = max(0, y - bw)
        y_bot = min(self.screen_h, y + bw)

        if y_top >= y_bot:
            return

        # Full-width beam
        mask[y_top:y_bot, :] = 255

        # Cut out the gap
        gap_top = max(0, gap_center - gap_size // 2)
        gap_bot = min(self.screen_h, gap_center + gap_size // 2)
        # Gap is in the vertical dimension for horizontal beams,
        # but actually the gap is a horizontal opening the player stands in.
        # For horizontal beams: the beam spans full width, the gap is in the Y position.
        # Re-think: horizontal beam moves vertically (down/up). It's a horizontal LINE.
        # The gap is a break in that line where the player can be safe.
        # So the gap is along the X axis.
        gap_left = max(0, gap_center - gap_size // 2)
        gap_right = min(self.screen_w, gap_center + gap_size // 2)
        mask[y_top:y_bot, gap_left:gap_right] = 0

    def _fill_v_beam_mask(self, mask, x_pos, gap_center, gap_size):
        """Fill vertical beam collision area (full height with gap)."""
        x = int(x_pos)
        bw = self.beam_width // 2
        x_left = max(0, x - bw)
        x_right = min(self.screen_w, x + bw)

        if x_left >= x_right:
            return

        mask[:, x_left:x_right] = 255

        # Gap along Y axis
        gap_top = max(0, gap_center - gap_size // 2)
        gap_bot = min(self.screen_h, gap_center + gap_size // 2)
        mask[gap_top:gap_bot, x_left:x_right] = 0

    def _fill_sweep_h_mask(self, mask):
        """Sweep beam: thin horizontal line, no gap."""
        y = int(self.pos)
        bw = self.beam_width // 2
        y_top = max(0, y - bw)
        y_bot = min(self.screen_h, y + bw)
        if y_top < y_bot:
            mask[y_top:y_bot, :] = 255

    def _fill_sweep_v_mask(self, mask):
        """Sweep beam: thin vertical line, no gap."""
        x = int(self.pos)
        bw = self.beam_width // 2
        x_left = max(0, x - bw)
        x_right = min(self.screen_w, x + bw)
        if x_left < x_right:
            mask[:, x_left:x_right] = 255

    # ────────────────────────────────────────────────────────────
    # Rendering
    # ────────────────────────────────────────────────────────────

    def render(self, surface):
        """
        Draw the beam (or warning indicator) onto a PyGame surface.
        The surface is at internal resolution (640×480).
        """
        if self.is_warning:
            self._render_warning(surface)
            return

        if self.beam_type == "horizontal":
            self._render_h_beam(surface, int(self.pos), self.gap_center,
                                self.gap_size, self.color)
        elif self.beam_type == "vertical":
            self._render_v_beam(surface, int(self.pos), self.gap_center,
                                self.gap_size, self.color)
        elif self.beam_type == "cross":
            self._render_h_beam(surface, int(self.h_pos), self.h_gap_center,
                                self.h_gap_size, self.color_h)
            self._render_v_beam(surface, int(self.v_pos), self.v_gap_center,
                                self.v_gap_size, self.color_v)
        elif self.beam_type == "sweep":
            if self.sweep_axis == "horizontal":
                self._render_sweep_h(surface)
            else:
                self._render_sweep_v(surface)

    def _render_warning(self, surface):
        """Draw a flashing indicator on the edge where the beam will arrive."""
        # Pulse alpha based on time
        pulse = abs(math.sin(self.warning_timer * 10)) * 0.7 + 0.3
        alpha = int(pulse * 180)

        warn_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        color_with_alpha = (*self._get_primary_color(), alpha)

        thickness = 6
        w, h = surface.get_size()

        if self.warn_edge == "top":
            pygame.draw.rect(warn_surf, color_with_alpha, (0, 0, w, thickness))
        elif self.warn_edge == "bottom":
            pygame.draw.rect(warn_surf, color_with_alpha, (0, h - thickness, w, thickness))
        elif self.warn_edge == "left":
            pygame.draw.rect(warn_surf, color_with_alpha, (0, 0, thickness, h))
        elif self.warn_edge == "right":
            pygame.draw.rect(warn_surf, color_with_alpha, (w - thickness, 0, thickness, h))

        surface.blit(warn_surf, (0, 0))

    def _get_primary_color(self):
        """Get the main color for this beam (for warnings)."""
        if self.beam_type == "horizontal":
            return self.color
        elif self.beam_type == "vertical":
            return self.color
        elif self.beam_type == "cross":
            return self.color_h
        elif self.beam_type == "sweep":
            return self.color
        return cfg.COLOR_LASER_HORIZONTAL

    def _render_h_beam(self, surface, y, gap_center, gap_size, color):
        """Render a horizontal beam with glow layers and gap."""
        w = surface.get_width()
        bw = self.beam_width // 2
        gap_left = gap_center - gap_size // 2
        gap_right = gap_center + gap_size // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Outer glow
        outer_bw = bw + cfg.BEAM_OUTER_GLOW
        outer_alpha = int(cfg.BEAM_OUTER_ALPHA * 255)
        outer_color = (*color, outer_alpha)
        # Left segment
        if gap_left > 0:
            pygame.draw.rect(glow_surf, outer_color, (0, y - outer_bw, gap_left, outer_bw * 2))
        # Right segment
        if gap_right < w:
            pygame.draw.rect(glow_surf, outer_color, (gap_right, y - outer_bw, w - gap_right, outer_bw * 2))

        # Inner glow
        inner_bw = bw + cfg.BEAM_INNER_GLOW
        inner_alpha = int(cfg.BEAM_INNER_ALPHA * 255)
        inner_color = (*color, inner_alpha)
        if gap_left > 0:
            pygame.draw.rect(glow_surf, inner_color, (0, y - inner_bw, gap_left, inner_bw * 2))
        if gap_right < w:
            pygame.draw.rect(glow_surf, inner_color, (gap_right, y - inner_bw, w - gap_right, inner_bw * 2))

        # Core beam
        core_alpha = 220
        core_color = (*color, core_alpha)
        if gap_left > 0:
            pygame.draw.rect(glow_surf, core_color, (0, y - bw, gap_left, bw * 2))
        if gap_right < w:
            pygame.draw.rect(glow_surf, core_color, (gap_right, y - bw, w - gap_right, bw * 2))

        surface.blit(glow_surf, (0, 0))

    def _render_v_beam(self, surface, x, gap_center, gap_size, color):
        """Render a vertical beam with glow layers and gap."""
        h = surface.get_height()
        bw = self.beam_width // 2
        gap_top = gap_center - gap_size // 2
        gap_bot = gap_center + gap_size // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Outer glow
        outer_bw = bw + cfg.BEAM_OUTER_GLOW
        outer_alpha = int(cfg.BEAM_OUTER_ALPHA * 255)
        outer_color = (*color, outer_alpha)
        if gap_top > 0:
            pygame.draw.rect(glow_surf, outer_color, (x - outer_bw, 0, outer_bw * 2, gap_top))
        if gap_bot < h:
            pygame.draw.rect(glow_surf, outer_color, (x - outer_bw, gap_bot, outer_bw * 2, h - gap_bot))

        # Inner glow
        inner_bw = bw + cfg.BEAM_INNER_GLOW
        inner_alpha = int(cfg.BEAM_INNER_ALPHA * 255)
        inner_color = (*color, inner_alpha)
        if gap_top > 0:
            pygame.draw.rect(glow_surf, inner_color, (x - inner_bw, 0, inner_bw * 2, gap_top))
        if gap_bot < h:
            pygame.draw.rect(glow_surf, inner_color, (x - inner_bw, gap_bot, inner_bw * 2, h - gap_bot))

        # Core
        core_alpha = 220
        core_color = (*color, core_alpha)
        if gap_top > 0:
            pygame.draw.rect(glow_surf, core_color, (x - bw, 0, bw * 2, gap_top))
        if gap_bot < h:
            pygame.draw.rect(glow_surf, core_color, (x - bw, gap_bot, bw * 2, h - gap_bot))

        surface.blit(glow_surf, (0, 0))

    def _render_sweep_h(self, surface):
        """Render a thin horizontal sweep beam (no gap)."""
        y = int(self.pos)
        w = surface.get_width()
        bw = self.beam_width // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        # Outer glow
        outer_bw = bw + 15
        pygame.draw.rect(glow_surf, (*self.color, int(cfg.BEAM_OUTER_ALPHA * 255)),
                         (0, y - outer_bw, w, outer_bw * 2))
        # Inner glow
        inner_bw = bw + 6
        pygame.draw.rect(glow_surf, (*self.color, int(cfg.BEAM_INNER_ALPHA * 255)),
                         (0, y - inner_bw, w, inner_bw * 2))
        # Core
        pygame.draw.rect(glow_surf, (*self.color, 230),
                         (0, y - bw, w, bw * 2))

        surface.blit(glow_surf, (0, 0))

    def _render_sweep_v(self, surface):
        """Render a thin vertical sweep beam (no gap)."""
        x = int(self.pos)
        h = surface.get_height()
        bw = self.beam_width // 2

        glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

        outer_bw = bw + 15
        pygame.draw.rect(glow_surf, (*self.color, int(cfg.BEAM_OUTER_ALPHA * 255)),
                         (x - outer_bw, 0, outer_bw * 2, h))
        inner_bw = bw + 6
        pygame.draw.rect(glow_surf, (*self.color, int(cfg.BEAM_INNER_ALPHA * 255)),
                         (x - inner_bw, 0, inner_bw * 2, h))
        pygame.draw.rect(glow_surf, (*self.color, 230),
                         (x - bw, 0, bw * 2, h))

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
        Returns (collided: bool, collision_point: tuple or None).
        collision_point is approximate (x, y) of first collision for
        particle spawning.
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
